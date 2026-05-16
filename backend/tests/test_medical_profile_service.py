import asyncio
import uuid

import pytest
from sqlalchemy import select

from db.database import Base, AsyncSessionLocal, engine
from models import medical_profile as medical_profile_models  # noqa: F401
from models import patient as patient_models  # noqa: F401
from models.medical_profile import BloodTestResult, MedicalProfile, PatientVector
from models.patient import AuditLog, Doctor, Patient, PatientAllergen, PatientCondition, PatientMedication
from services.medical_profile_service import MedicalProfileService


@pytest.fixture(autouse=True)
def reset_database() -> None:
    async def _reset() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())


def test_normalisation_synonym_expansion_and_constraint_builder() -> None:
    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            service = MedicalProfileService(db)
            conditions = service.normalise_conditions(["High BP", "T2DM"])
            allergens = service.expand_allergen_synonyms(["milk"])
            rules = service.resolve_medication_rules(["Metformin 500mg"])
            constraints = service.build_constraints(conditions, allergens, rules)

            assert conditions == ["hypertension", "type 2 diabetes"]
            assert "dairy" in allergens
            assert "casein" in allergens
            assert "sugary drinks" in constraints["avoid"]
            assert "sodium" in constraints["limit"]
            assert "take carbohydrate distribution into account" in constraints["limit"]

    asyncio.run(_run())


def test_build_medical_profile_upserts_profile_vector_and_audit() -> None:
    async def _run() -> None:
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(Doctor(id=doctor_id, email="doc@example.com", name="Dr Test"))
            db.add(Patient(id=patient_id, doctor_id=doctor_id, patient_code="PAT-20260001", first_name="Mina", last_name="Patel"))
            db.add(PatientCondition(patient_id=patient_id, name="high bp"))
            db.add(PatientAllergen(patient_id=patient_id, name="milk", severity="high"))
            db.add(PatientMedication(patient_id=patient_id, name="Metformin"))
            db.add(BloodTestResult(patient_id=patient_id, marker_name="HbA1c", value=8.1, unit="%", reference_range="4-5.6", is_abnormal=True))
            await db.commit()

            profile = await MedicalProfileService(db).build_medical_profile(patient_id)
            await db.commit()

            assert profile.conditions == ["hypertension"]
            assert "dairy" in profile.allergens
            assert "HbA1c".lower() in [marker.lower() for marker in profile.abnormal_markers]

            saved_profile = await db.get(MedicalProfile, profile.id)
            assert saved_profile is not None
            vector = await db.scalar(select(PatientVector).where(PatientVector.patient_id == patient_id))
            assert vector is not None
            audit_log = await db.scalar(select(AuditLog).where(AuditLog.action == "medical_profile_built"))
            assert audit_log is not None

    asyncio.run(_run())
