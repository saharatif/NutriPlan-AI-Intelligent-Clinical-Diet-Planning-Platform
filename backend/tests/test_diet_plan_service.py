import asyncio
import uuid

import pytest
from sqlalchemy import select

from db.database import AsyncSessionLocal, Base, engine
from models import diet_plan as diet_plan_models  # noqa: F401
from models import medical_profile as medical_profile_models  # noqa: F401
from models import patient as patient_models  # noqa: F401
from models.diet_plan import DietPlanMeal
from models.medical_profile import MedicalProfile
from models.patient import AuditLog, Doctor, Patient, PatientAllergen, PatientCondition, PatientMedication
from services.allergen_service import AllergenService
from services.diet_plan_service import DietPlanService
from services.no_repeat_service import NoRepeatService


@pytest.fixture(autouse=True)
def reset_database() -> None:
    async def _reset() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())


def test_generate_plan_for_patient_has_112_safe_non_repeating_meals() -> None:
    async def _run() -> None:
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(Doctor(id=doctor_id, email="doc@example.com", name="Dr Test"))
            db.add(Patient(id=patient_id, doctor_id=doctor_id, patient_code="PAT-20260001", first_name="Mina", last_name="Patel"))
            db.add(PatientCondition(patient_id=patient_id, name="hypertension"))
            db.add(PatientCondition(patient_id=patient_id, name="hypothyroid"))
            db.add(PatientAllergen(patient_id=patient_id, name="milk", severity="high"))
            db.add(PatientMedication(patient_id=patient_id, name="Atorvastatin"))
            await db.flush()
            db.add(
                MedicalProfile(
                    patient_id=patient_id,
                    conditions=["hypertension", "hypothyroid"],
                    allergens=["milk", "dairy", "whey", "casein", "lactose"],
                    medications=["Atorvastatin"],
                    abnormal_markers=[],
                    medication_rules=["limit grapefruit unless clinician approves"],
                    nutrition_constraints={"avoid": ["milk", "soy", "grapefruit"], "limit": ["sodium"], "prefer": []},
                )
            )
            await db.commit()

            plan = await DietPlanService(db).generate_plan(patient_id, selected_favourites=["Dal"], plan_type="therapeutic")
            await db.commit()

            assert plan.status == "draft"
            assert len(plan.meals) == 112
            assert all(meal.meal_name and meal.base_calories and meal.ingredients for meal in plan.meals)
            assert sum(1 for meal in plan.meals if meal.recipe_url) / len(plan.meals) >= 0.6
            assert any("low sodium" in (meal.clinical_note or "") for meal in plan.meals)
            assert any("no grapefruit" in (meal.clinical_note or "") for meal in plan.meals)
            assert any("soy avoided" in (meal.clinical_note or "") for meal in plan.meals)

            meal_dicts = [
                {
                    "week": meal.week,
                    "meal_name": meal.meal_name,
                    "ingredients": meal.ingredients,
                }
                for meal in plan.meals
            ]
            assert AllergenService().validate_plan_allergens(meal_dicts, ["milk", "soy", "grapefruit"]) == []
            assert NoRepeatService().validate_plan_no_repeats(meal_dicts) == []
            audit_log = await db.scalar(select(AuditLog).where(AuditLog.action == "diet_plan_generation_completed"))
            assert audit_log is not None

    asyncio.run(_run())


def test_regenerate_single_meal_replaces_only_target() -> None:
    async def _run() -> None:
        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(Doctor(id=doctor_id, email="doc@example.com", name="Dr Test"))
            db.add(Patient(id=patient_id, doctor_id=doctor_id, patient_code="PAT-20260001", first_name="Mina", last_name="Patel"))
            db.add(PatientAllergen(patient_id=patient_id, name="peanut"))
            await db.commit()

            plan = await DietPlanService(db).generate_plan(patient_id)
            await db.commit()
            before = {meal.id: meal.meal_name for meal in plan.meals}
            target = plan.meals[0]
            regenerated = await DietPlanService(db).regenerate_meal(plan.id, target.id, doctor_id)
            await db.commit()

            result = await db.execute(select(DietPlanMeal).where(DietPlanMeal.diet_plan_id == plan.id))
            after = {meal.id: meal.meal_name for meal in result.scalars()}
            changed = [meal_id for meal_id, name in after.items() if before[meal_id] != name]
            assert changed == [regenerated.id]

    asyncio.run(_run())
