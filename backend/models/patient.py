import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Sex(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class AuditEvent(str, enum.Enum):
    doctor_login = "doctor_login"
    doctor_logout = "doctor_logout"
    patient_created = "patient_created"
    patient_updated = "patient_updated"
    patient_deleted = "patient_deleted"
    document_uploaded = "document_uploaded"
    ocr_completed = "ocr_completed"
    medical_profile_built = "medical_profile_built"
    diet_plan_generation_started = "diet_plan_generation_started"
    diet_plan_generation_completed = "diet_plan_generation_completed"
    meal_regenerated = "meal_regenerated"
    plan_approved = "plan_approved"
    pdf_exported = "pdf_exported"
    allergen_violation_detected = "allergen_violation_detected"
    no_repeat_violation_detected = "no_repeat_violation_detected"


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    clinic: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patients: Mapped[list["Patient"]] = relationship(back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (UniqueConstraint("doctor_id", "patient_code", name="uq_patient_code_per_doctor"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, index=True)
    patient_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    sex: Mapped[Sex | None] = mapped_column(Enum(Sex, name="sex"))
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(320))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    doctor: Mapped[Doctor] = relationship(back_populates="patients")
    conditions: Mapped[list["PatientCondition"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    medications: Mapped[list["PatientMedication"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    allergens: Mapped[list["PatientAllergen"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    family_history: Mapped[list["PatientFamilyHistory"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    favourite_foods: Mapped[list["PatientFavouriteFood"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    documents: Mapped[list["PatientDocument"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    diagnosed_at: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)


class PatientMedication(Base):
    __tablename__ = "patient_medications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(120))
    frequency: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class PatientAllergen(Base):
    __tablename__ = "patient_allergens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(60), default="manual")


class PatientFamilyHistory(Base):
    __tablename__ = "patient_family_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    condition: Mapped[str] = mapped_column(String(160), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)


class PatientFavouriteFood(Base):
    __tablename__ = "patient_favourite_foods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    preference_level: Mapped[int] = mapped_column(Integer, default=1)


class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), default="application/pdf")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    ocr_status: Mapped[str] = mapped_column(String(40), default="pending")
    ocr_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    ocr_error: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
