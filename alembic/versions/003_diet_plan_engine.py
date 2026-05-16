"""diet plan engine

Revision ID: 003_diet_plan_engine
Revises: 002_medical_profile
Create Date: 2026-05-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_diet_plan_engine"
down_revision: str | None = "002_medical_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("diet_plans", sa.Column("plan_type", sa.String(80), server_default="standard", nullable=False))
    op.add_column("diet_plans", sa.Column("selected_favourites", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("diet_plans", sa.Column("generation_metadata", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("diet_plans", sa.Column("approved_at", sa.DateTime(timezone=True)))
    op.add_column("diet_plans", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    op.create_table(
        "diet_plan_meals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("diet_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("diet_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("meal_slot", sa.String(40), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("meal_name", sa.String(180), nullable=False),
        sa.Column("base_calories", sa.Integer(), nullable=False),
        sa.Column("base_protein_g", sa.Float(), nullable=False),
        sa.Column("base_fat_g", sa.Float(), nullable=False),
        sa.Column("base_carbs_g", sa.Float(), nullable=False),
        sa.Column("ingredients", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("recipe_url", sa.String(500)),
        sa.Column("clinical_note", sa.Text()),
        sa.Column("serving_multiplier", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("diet_plan_id", "week", "day", "meal_slot", name="uq_diet_plan_meal_slot"),
    )
    op.create_index("ix_diet_plan_meals_diet_plan_id", "diet_plan_meals", ["diet_plan_id"])
    op.create_index("ix_diet_plan_meals_patient_id", "diet_plan_meals", ["patient_id"])

    op.create_table(
        "recipe_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_name", sa.String(180), nullable=False, unique=True),
        sa.Column("ingredients", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("base_calories", sa.Integer(), nullable=False),
        sa.Column("base_protein_g", sa.Float(), nullable=False),
        sa.Column("base_fat_g", sa.Float(), nullable=False),
        sa.Column("base_carbs_g", sa.Float(), nullable=False),
        sa.Column("recipe_url", sa.String(500)),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recipe_library")
    op.drop_table("diet_plan_meals")
    op.drop_column("diet_plans", "updated_at")
    op.drop_column("diet_plans", "approved_at")
    op.drop_column("diet_plans", "generation_metadata")
    op.drop_column("diet_plans", "selected_favourites")
    op.drop_column("diet_plans", "plan_type")
