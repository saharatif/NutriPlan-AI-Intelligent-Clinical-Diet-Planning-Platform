import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BloodTestResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    document_id: uuid.UUID | None = None
    marker_name: str
    value: float | None = None
    unit: str | None = None
    reference_range: str | None = None
    is_abnormal: bool
    raw_text: str | None = None
    created_at: datetime


class OcrResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    document_id: uuid.UUID
    raw_text: str
    parsed_json: dict
    status: str
    created_at: datetime


class MedicalProfilePayload(BaseModel):
    conditions: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    abnormal_markers: list[str] = Field(default_factory=list)
    medication_rules: list[str] = Field(default_factory=list)
    nutrition_constraints: dict[str, list[str]] = Field(default_factory=lambda: {"avoid": [], "limit": [], "prefer": []})


class MedicalProfileRead(MedicalProfilePayload):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    embedding_text: str | None = None
    updated_at: datetime
