"""native pgvector embedding column

Revision ID: 003_pgvector
Revises: 003_diet_plan_engine
Create Date: 2026-05-16
"""

from collections.abc import Sequence

from alembic import op

revision: str = "003_pgvector"
down_revision: str | None = "003_diet_plan_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        ALTER TABLE patient_vectors
        ADD COLUMN IF NOT EXISTS embedding vector(1536)
    """)

    # Migrate existing JSON vectors to the native column
    op.execute("""
        UPDATE patient_vectors
        SET embedding = vector::text::vector
        WHERE vector IS NOT NULL
          AND vector::text NOT IN ('[]', 'null')
          AND embedding IS NULL
    """)

    # Temporarily increase maintenance_work_mem for index creation.
    # lists=10 is correct for small datasets (<10 000 vectors).
    # Supabase free tier caps maintenance_work_mem at 32 MB by default.
    op.execute("SET LOCAL maintenance_work_mem = '64MB'")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_patient_vectors_embedding
        ON patient_vectors
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_patient_vectors_embedding")
    op.execute("ALTER TABLE patient_vectors DROP COLUMN IF EXISTS embedding")
