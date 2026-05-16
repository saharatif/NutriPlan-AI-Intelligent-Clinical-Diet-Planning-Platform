import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), default="generating")
    plan_type: Mapped[str] = mapped_column(String(80), default="standard")
    selected_favourites: Mapped[list] = mapped_column(JSON, default=list)
    generation_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meals: Mapped[list["DietPlanMeal"]] = relationship(cascade="all, delete-orphan", lazy="selectin", order_by="DietPlanMeal.sequence")


class DietPlanMeal(Base):
    __tablename__ = "diet_plan_meals"
    __table_args__ = (UniqueConstraint("diet_plan_id", "week", "day", "meal_slot", name="uq_diet_plan_meal_slot"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diet_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("diet_plans.id", ondelete="CASCADE"), index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    meal_slot: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    meal_name: Mapped[str] = mapped_column(String(180), nullable=False)
    base_calories: Mapped[int] = mapped_column(Integer, nullable=False)
    base_protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    base_fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    base_carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    ingredients: Mapped[list] = mapped_column(JSON, default=list)
    recipe_url: Mapped[str | None] = mapped_column(String(500))
    clinical_note: Mapped[str | None] = mapped_column(Text)
    serving_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecipeLibrary(Base):
    __tablename__ = "recipe_library"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_name: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    ingredients: Mapped[list] = mapped_column(JSON, default=list)
    base_calories: Mapped[int] = mapped_column(Integer, nullable=False)
    base_protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    base_fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    base_carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    recipe_url: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[list] = mapped_column(JSON, default=list)
