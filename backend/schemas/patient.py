import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.patient import Sex


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str
    clinic: str | None = None


class ConditionBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    diagnosed_at: date | None = None
    notes: str | None = None


class MedicationBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    dosage: str | None = None
    frequency: str | None = None
    notes: str | None = None


class AllergenBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    severity: str | None = None
    source: str = "manual"


class FamilyHistoryBase(BaseModel):
    condition: str = Field(min_length=1, max_length=160)
    relationship: str | None = None
    notes: str | None = None


class FavouriteFoodBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    preference_level: int = Field(default=1, ge=1, le=5)


class ChildReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class ConditionRead(ChildReadMixin, ConditionBase):
    pass


class MedicationRead(ChildReadMixin, MedicationBase):
    pass


class AllergenRead(ChildReadMixin, AllergenBase):
    pass


class FamilyHistoryRead(ChildReadMixin, FamilyHistoryBase):
    pass


class FavouriteFoodRead(ChildReadMixin, FavouriteFoodBase):
    pass


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    storage_path: str
    content_type: str
    size_bytes: int
    ocr_status: str
    ocr_processed: bool
    ocr_error: str | None = None
    uploaded_at: datetime


DIETARY_PREFERENCES = {"vegan", "vegetarian", "pescatarian", "flexitarian"}


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    sex: Sex | None = None
    height_cm: float | None = Field(default=None, gt=0, lt=300)
    weight_kg: float | None = Field(default=None, gt=0, lt=700)
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None
    ethnicity: str | None = Field(default=None, max_length=120)
    dietary_preference: str | None = Field(default=None, max_length=40)


class PatientCreate(PatientBase):
    conditions: list[ConditionBase] = []
    medications: list[MedicationBase] = []
    allergens: list[AllergenBase] = []
    family_history: list[FamilyHistoryBase] = []
    favourite_foods: list[FavouriteFoodBase] = []


class PatientUpdate(PatientBase):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    conditions: list[ConditionBase] | None = None
    medications: list[MedicationBase] | None = None
    allergens: list[AllergenBase] | None = None
    family_history: list[FamilyHistoryBase] | None = None
    favourite_foods: list[FavouriteFoodBase] | None = None


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_code: str
    created_at: datetime
    updated_at: datetime
    conditions: list[ConditionRead] = []
    medications: list[MedicationRead] = []
    allergens: list[AllergenRead] = []
    family_history: list[FamilyHistoryRead] = []
    favourite_foods: list[FavouriteFoodRead] = []
    documents: list[DocumentRead] = []


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_code: str
    first_name: str
    last_name: str
    created_at: datetime
