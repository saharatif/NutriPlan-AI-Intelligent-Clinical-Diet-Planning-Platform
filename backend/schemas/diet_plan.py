import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str


class MealBase(BaseModel):
    meal_name: str
    base_calories: int
    base_protein_g: float
    base_fat_g: float
    base_carbs_g: float
    ingredients: list[Ingredient]
    recipe_url: str | None = None
    clinical_note: str | None = None
    serving_multiplier: float = 1.0


class DietPlanMealRead(MealBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diet_plan_id: uuid.UUID
    patient_id: uuid.UUID
    week: int
    day: int
    meal_slot: str
    sequence: int


class DietPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    status: str
    plan_type: str
    selected_favourites: list[str] = []
    generation_metadata: dict = {}
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    meals: list[DietPlanMealRead] = []


class DietPlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    status: str
    plan_type: str
    created_at: datetime


class GenerateDietPlanRequest(BaseModel):
    selected_favourites: list[str] = Field(default_factory=list)
    plan_type: str = "standard"


class ServingMultiplierUpdate(BaseModel):
    serving_multiplier: float = Field(gt=0, le=5)
