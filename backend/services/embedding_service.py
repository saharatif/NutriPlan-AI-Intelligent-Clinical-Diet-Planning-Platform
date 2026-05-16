import hashlib
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from db.pinecone_client import VectorClient
from utils.config import settings

CHUNK_SIZE = 400     # characters per chunk
CHUNK_OVERLAP = 80   # overlap keeps markers from being split across chunk boundaries


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping chunks, snapping boundaries to the nearest
    newline so individual blood-marker rows are never cut mid-line.
    """
    chunks, start, idx = [], 0, 0
    while start < len(text):
        end = start + size
        snippet = text[start:end]
        if end < len(text):
            nl = snippet.rfind("\n")
            if nl > size // 2:          # only snap if the newline is in the second half
                end = start + nl
                snippet = text[start:end]
        snippet = snippet.strip()
        if snippet:
            chunks.append({"index": idx, "text": snippet})
        start = end - overlap
        idx += 1
    return chunks


class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def embed_text(self, text: str) -> list[float]:
        if not settings.OPENAI_API_KEY:
            return self._deterministic_embedding(text)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "text-embedding-3-small", "input": text},
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single OpenAI API call."""
        if not settings.OPENAI_API_KEY:
            return [self._deterministic_embedding(t) for t in texts]

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": "text-embedding-3-small", "input": texts},
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in data]

    async def update_patient_embedding(
        self, patient_id: uuid.UUID, embedding_text: str, metadata: dict
    ) -> list[float]:
        """Embed the medical profile summary and store as a single patient vector."""
        vector = await self.embed_text(embedding_text)
        await VectorClient(self.db).upsert(patient_id, vector, metadata)
        return vector

    async def embed_and_store_document(
        self,
        document_id: uuid.UUID,
        patient_id: uuid.UUID,
        raw_text: str,
    ) -> int:
        """
        Chunk OCR text, embed each chunk, and store all chunks in Pinecone
        (or pgvector fallback).  Returns the number of chunks stored.
        """
        chunks = chunk_text(raw_text)
        if not chunks:
            return 0

        # Embed in batches of 20 to stay within OpenAI rate limits
        BATCH = 20
        chunk_vectors: list[dict] = []
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            vectors = await self.embed_batch([c["text"] for c in batch])
            for chunk, vector in zip(batch, vectors):
                chunk_vectors.append({"index": chunk["index"], "text": chunk["text"], "vector": vector})

        await VectorClient(self.db).upsert_document_chunks(document_id, patient_id, chunk_vectors)
        return len(chunk_vectors)

    def _deterministic_embedding(self, text: str, dimensions: int = 1536) -> list[float]:
        """Offline fallback for tests — no OpenAI call required."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = list(digest)
        return [((values[i % len(values)] / 255.0) * 2) - 1 for i in range(dimensions)]
