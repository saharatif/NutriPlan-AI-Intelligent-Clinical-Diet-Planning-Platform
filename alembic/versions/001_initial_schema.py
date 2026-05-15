"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    sex_enum = postgresql.ENUM("male", "female", "other", name="sex")
    sex_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("clinic", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("patient_code", sa.String(32), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("sex", sex_enum),
        sa.Column("height_cm", sa.Float),
        sa.Column("weight_kg", sa.Float),
        sa.Column("phone", sa.String(40)),
        sa.Column("email", sa.String(320)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("doctor_id", "patient_code", name="uq_patient_code_per_doctor"),
    )
    op.create_index("ix_patients_doctor_id", "patients", ["doctor_id"])
    op.create_index("ix_patients_patient_code", "patients", ["patient_code"])

    for table, cols in {
        "patient_conditions": [sa.Column("name", sa.String(160), nullable=False), sa.Column("diagnosed_at", sa.Date), sa.Column("notes", sa.Text)],
        "patient_medications": [sa.Column("name", sa.String(160), nullable=False), sa.Column("dosage", sa.String(120)), sa.Column("frequency", sa.String(120)), sa.Column("notes", sa.Text)],
        "patient_allergens": [sa.Column("name", sa.String(160), nullable=False), sa.Column("severity", sa.String(60)), sa.Column("source", sa.String(60), server_default="manual", nullable=False)],
        "patient_family_history": [sa.Column("condition", sa.String(160), nullable=False), sa.Column("relationship", sa.String(100)), sa.Column("notes", sa.Text)],
        "patient_favourite_foods": [sa.Column("name", sa.String(160), nullable=False), sa.Column("preference_level", sa.Integer, server_default="1", nullable=False)],
    }.items():
        op.create_table(
            table,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
            *cols,
        )
        op.create_index(f"ix_{table}_patient_id", table, ["patient_id"])

    op.create_table(
        "patient_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(120), server_default="application/pdf", nullable=False),
        sa.Column("size_bytes", sa.Integer, server_default="0", nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_patient_documents_patient_id", "patient_documents", ["patient_id"])

    op.create_table(
        "diet_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("status", sa.String(40), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_diet_plans_doctor_id", "diet_plans", ["doctor_id"])
    op.create_index("ix_diet_plans_patient_id", "diet_plans", ["patient_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id")),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_doctor_id", "audit_logs", ["doctor_id"])


def downgrade() -> None:
    for table in [
        "audit_logs",
        "diet_plans",
        "patient_documents",
        "patient_favourite_foods",
        "patient_family_history",
        "patient_allergens",
        "patient_medications",
        "patient_conditions",
        "patients",
        "doctors",
    ]:
        op.drop_table(table)
    postgresql.ENUM(name="sex").drop(op.get_bind(), checkfirst=True)
