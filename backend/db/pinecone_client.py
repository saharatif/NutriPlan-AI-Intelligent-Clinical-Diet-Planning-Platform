"""
VectorClient — dual-backend vector store abstraction.

VECTOR_BACKEND=pgvector (default / primary)
    Stores embeddings in patient_vectors.embedding (native pgvector column).
    Similarity search uses PostgreSQL <=> cosine distance operator.
    Runs entirely inside Supabase — no external service required.

VECTOR_BACKEND=pinecone
    Stores embeddings in Pinecone AND writes a copy to patient_vectors
    so the DB stays consistent.
"""

import json
import math
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.medical_profile import PatientVector
from utils.config import settings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot    = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

_PINECONE_BATCH = 20


def _vec_literal(vector: list[float]) -> str:
    """
    Format a Python float list as a PostgreSQL vector literal.
    Embedded directly in SQL strings (not as a parameter) to avoid
    asyncpg's prepared-statement parser misinterpreting '::vector'.
    Safe because values are always floats from OpenAI embeddings.
    """
    return "[" + ",".join(f"{v:.8f}" for v in vector) + "]"


def _pinecone_index():
    from pinecone import Pinecone  # noqa: PLC0415
    return Pinecone(api_key=settings.PINECONE_API_KEY).Index(settings.PINECONE_INDEX_NAME)


class VectorClient:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._use_pinecone = settings.VECTOR_BACKEND == "pinecone"
        # Detect SQLite (test environment) — pgvector syntax not supported there
        from db.database import engine  # noqa: PLC0415
        self._is_sqlite = engine.dialect.name == "sqlite"

    # ── Patient profile vector ────────────────────────────────────────────────

    # ── SQLite fallback (tests only) ──────────────────────────────────────────

    async def _sqlite_upsert(self, patient_id: uuid.UUID, vector: list[float], metadata: dict) -> PatientVector:
        existing = await self.db.scalar(select(PatientVector).where(PatientVector.patient_id == patient_id))
        if existing is None:
            existing = PatientVector(patient_id=patient_id, vector=vector, metadata_json=metadata)
            self.db.add(existing)
        else:
            existing.vector = vector
            existing.metadata_json = metadata
        await self.db.flush()
        return existing

    async def _sqlite_query(self, vector: list[float], top_k: int, filter: dict | None) -> list[dict]:
        rows = list((await self.db.execute(select(PatientVector))).scalars())
        if filter:
            rows = [r for r in rows if all(r.metadata_json.get(k) == v for k, v in filter.items())]
        scored = sorted(rows, key=lambda r: _cosine_similarity(vector, r.vector), reverse=True)
        return [{"patient_id": str(r.patient_id), "score": _cosine_similarity(vector, r.vector), "metadata": r.metadata_json} for r in scored[:top_k]]

    # ── Patient profile vector ────────────────────────────────────────────────

    async def upsert(self, patient_id: uuid.UUID, vector: list[float], metadata: dict) -> PatientVector:
        """Store / update the medical-profile summary vector for a patient."""
        if self._is_sqlite:
            return await self._sqlite_upsert(patient_id, vector, metadata)

        vec    = _vec_literal(vector)
        pid    = str(patient_id)
        meta   = json.dumps(metadata)
        # Use json.dumps for the JSON array so it's valid PostgreSQL jsonb
        vec_json = json.dumps(vector)

        existing = await self.db.scalar(
            select(PatientVector).where(PatientVector.patient_id == patient_id)
        )

        if existing is None:
            await self.db.execute(text(f"""
                INSERT INTO patient_vectors (id, patient_id, vector, embedding, metadata_json)
                VALUES (
                    gen_random_uuid(),
                    '{pid}'::uuid,
                    '{vec_json}'::jsonb,
                    '{vec}'::vector,
                    '{meta}'::jsonb
                )
            """))
        else:
            await self.db.execute(text(f"""
                UPDATE patient_vectors
                SET embedding   = '{vec}'::vector,
                    vector      = '{vec_json}'::jsonb,
                    updated_at  = now()
                WHERE patient_id = '{pid}'::uuid
                  AND (metadata_json->>'type' IS DISTINCT FROM 'document_chunk')
            """))

        if self._use_pinecone:
            _pinecone_index().upsert(
                vectors=[{"id": f"patient_{patient_id}", "values": vector, "metadata": metadata}],
                namespace="patients",
            )

        await self.db.flush()
        return await self.db.scalar(
            select(PatientVector).where(PatientVector.patient_id == patient_id)
        )  # type: ignore[return-value]

    async def query(self, vector: list[float], top_k: int = 5, filter: dict | None = None) -> list[dict]:
        """Semantic search using Supabase pgvector <=> cosine distance operator."""
        if self._is_sqlite:
            return await self._sqlite_query(vector, top_k, filter)

        vec = _vec_literal(vector)
        rows = (await self.db.execute(text(f"""
            SELECT patient_id,
                   metadata_json,
                   1 - (embedding <=> '{vec}'::vector) AS score
            FROM patient_vectors
            WHERE embedding IS NOT NULL
              AND (metadata_json->>'type' IS DISTINCT FROM 'document_chunk')
            ORDER BY embedding <=> '{vec}'::vector
            LIMIT {int(top_k)}
        """))).fetchall()

        results = [
            {"patient_id": str(row.patient_id), "score": float(row.score), "metadata": row.metadata_json}
            for row in rows
        ]
        if filter:
            results = [r for r in results if all(r["metadata"].get(k) == v for k, v in filter.items())]
        return results

    # ── Document chunk vectors ────────────────────────────────────────────────

    async def upsert_document_chunks(
        self,
        document_id: uuid.UUID,
        patient_id: uuid.UUID,
        chunks: list[dict],
    ) -> None:
        """Store chunked OCR vectors in Supabase pgvector or Pinecone."""
        if not chunks:
            return

        if self._is_sqlite:
            return  # SQLite test env: skip chunk storage

        if self._use_pinecone:
            index = _pinecone_index()
            namespace = f"patient-{patient_id}"
            vectors = [
                {
                    "id": f"{document_id}-chunk-{c['index']}",
                    "values": c["vector"],
                    "metadata": {
                        "patient_id":  str(patient_id),
                        "document_id": str(document_id),
                        "chunk_index": c["index"],
                        "chunk_text":  c["text"][:500],
                    },
                }
                for c in chunks
            ]
            for i in range(0, len(vectors), _PINECONE_BATCH):
                index.upsert(vectors=vectors[i: i + _PINECONE_BATCH], namespace=namespace)
            return

        # pgvector: one row per chunk, keyed by document+chunk
        for c in chunks:
            chunk_id = uuid.uuid5(uuid.UUID(str(document_id)), f"chunk-{c['index']}")
            meta = {
                "patient_id":  str(patient_id),
                "document_id": str(document_id),
                "chunk_index": c["index"],
                "chunk_text":  c["text"][:500],
                "type":        "document_chunk",
            }
            vec_literal = _vec_literal(c["vector"])
            vec_json    = json.dumps(c["vector"])
            meta_json   = json.dumps(meta).replace("'", "''")  # escape single quotes
            await self.db.execute(text(f"""
                INSERT INTO patient_vectors (id, patient_id, vector, embedding, metadata_json)
                VALUES (
                    '{chunk_id}'::uuid,
                    '{patient_id}'::uuid,
                    '{vec_json}'::jsonb,
                    '{vec_literal}'::vector,
                    '{meta_json}'::jsonb
                )
                ON CONFLICT DO NOTHING
            """))

    async def query_document_chunks(
        self,
        query_vector: list[float],
        patient_id: uuid.UUID,
        top_k: int = 5,
    ) -> list[dict]:
        """Retrieve the most relevant document chunks using pgvector similarity."""
        vec = _vec_literal(query_vector)
        rows = (await self.db.execute(text(f"""
            SELECT metadata_json,
                   1 - (embedding <=> '{vec}'::vector) AS score
            FROM patient_vectors
            WHERE patient_id  = '{patient_id}'::uuid
              AND embedding    IS NOT NULL
              AND metadata_json->>'type' = 'document_chunk'
            ORDER BY embedding <=> '{vec}'::vector
            LIMIT {int(top_k)}
        """))).fetchall()

        return [
            {
                "score":      float(row.score),
                "chunk_text": row.metadata_json.get("chunk_text", ""),
                "metadata":   row.metadata_json,
            }
            for row in rows
        ]
