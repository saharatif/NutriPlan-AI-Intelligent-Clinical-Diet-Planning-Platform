"""medical profile and ocr tables

Revision ID: 002_medical_profile
Revises: 001_initial_schema
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_medical_profile"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patient_documents", sa.Column("ocr_status", sa.String(40), server_default="pending", nullable=False))
    op.add_column("patient_documents", sa.Column("ocr_processed", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("patient_documents", sa.Column("ocr_error", sa.Text()))
    op.add_column("audit_logs", sa.Column("metadata_json", sa.JSON()))

    op.create_table(
        "blood_test_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_documents.id", ondelete="SET NULL")),
        sa.Column("marker_name", sa.String(160), nullable=False),
        sa.Column("value", sa.Float()),
        sa.Column("unit", sa.String(60)),
        sa.Column("reference_range", sa.String(120)),
        sa.Column("is_abnormal", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_blood_test_results_patient_id", "blood_test_results", ["patient_id"])
    op.create_index("ix_blood_test_results_document_id", "blood_test_results", ["document_id"])

    op.create_table(
        "ocr_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("parsed_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(40), server_default="completed", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ocr_results_patient_id", "ocr_results", ["patient_id"])
    op.create_index("ix_ocr_results_document_id", "ocr_results", ["document_id"])

    op.create_table(
        "medical_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conditions", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("allergens", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("medications", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("abnormal_markers", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("medication_rules", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("nutrition_constraints", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("embedding_text", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("patient_id", name="uq_medical_profiles_patient_id"),
    )
    op.create_index("ix_medical_profiles_patient_id", "medical_profiles", ["patient_id"])

    op.create_table(
        "patient_vectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vector", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("patient_id", name="uq_patient_vectors_patient_id"),
    )
    op.create_index("ix_patient_vectors_patient_id", "patient_vectors", ["patient_id"])


def downgrade() -> None:
    op.drop_table("patient_vectors")
    op.drop_table("medical_profiles")
    op.drop_table("ocr_results")
    op.drop_table("blood_test_results")
    op.drop_column("audit_logs", "metadata_json")
    op.drop_column("patient_documents", "ocr_error")
    op.drop_column("patient_documents", "ocr_processed")
    op.drop_column("patient_documents", "ocr_status")
