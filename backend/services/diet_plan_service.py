import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.diet_plan import DietPlan, DietPlanMeal
from models.medical_profile import MedicalProfile
from models.patient import AuditEvent, Patient, PatientAllergen, PatientCondition, PatientMedication
from services.allergen_service import AllergenService
from services.audit_service import log
from services.medical_profile_service import MedicalProfileService
from services.no_repeat_service import NoRepeatService
from services.openai_diet_service import OpenAIDietService
from services.recipe_service import RecipeService

MEAL_SLOTS = ["Breakfast", "Lunch", "Snack", "Dinner"]


def _parse_num_weeks(plan_type: str) -> int:
    """Extract week count from plan_type string e.g. '2-week' → 2, '4-week' → 4."""
    if plan_type.startswith("2"):
        return 2
    return 4

# Offset applied to sequence when regenerating a single meal so the replacement
# dish is drawn from a different position in the BASE_DISHES rotation than the
# original, guaranteeing a different name without re-running full generation.
_REGEN_OFFSET = 997
BASE_DISHES = [
    "Quinoa Lentil Bowl", "Herbed Salmon Plate", "Chickpea Garden Wrap", "Turkey Avocado Salad",
    "Berry Chia Oats", "Chicken Brown Rice Bowl", "Roasted Vegetable Plate", "Bean Sweet Potato Stew",
    "Apple Seed Parfait", "Zucchini Herb Skillet", "Broccoli Citrus Bowl", "Cauliflower Rice Plate",
    "Pumpkin Seed Snack Box", "Lemon Herb Chicken", "Mediterranean Lentil Salad", "Spinach Bean Soup",
    "Avocado Tomato Toast", "Carrot Ginger Bowl", "Cucumber Turkey Roll", "Berries Oat Crunch",
    "Salmon Greens Plate", "Chickpea Quinoa Salad", "Sweet Potato Bean Bowl", "Herb Vegetable Soup",
    "Chicken Spinach Plate", "Lentil Cucumber Bowl", "Brown Rice Garden Plate", "Apple Chia Snack",
]


class DietPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.allergen_service = AllergenService()
        self.no_repeat_service = NoRepeatService()
        self.openai_diet_service = OpenAIDietService()
        self.recipe_service = RecipeService()
        self.condition_rules = self._load_json("condition_rules.json")
        self.medication_rules = self._load_json("medication_rules.json")

    async def generate_plan(
        self,
        patient_id: uuid.UUID,
        selected_favourites: list[str] | None = None,
        plan_type: str = "standard",
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> DietPlan:
        patient = await self.db.get(Patient, patient_id)
        if patient is None:
            raise ValueError("Patient not found")
        selected_favourites = selected_favourites or []
        num_weeks = _parse_num_weeks(plan_type)
        profile = await self._get_or_build_profile(patient_id)
        allergens = list(profile.allergens or [])
        conditions = list(profile.conditions or [])
        medications = list(profile.medications or [])
        restrictions = self._medical_restrictions(conditions, medications)
        ethnicity = patient.ethnicity or None
        dietary_preference = patient.dietary_preference or None

        plan = DietPlan(
            doctor_id=patient.doctor_id,
            patient_id=patient_id,
            status="generating",
            plan_type=plan_type,
            selected_favourites=selected_favourites,
            generation_metadata={
                "conditions": conditions,
                "restrictions": restrictions,
                "num_weeks": num_weeks,
                "ethnicity": ethnicity,
                "dietary_preference": dietary_preference,
                "provider": "openai" if self.openai_diet_service.is_enabled() else "deterministic",
            },
        )
        self.db.add(plan)
        await self.db.flush()

        meals = await self._build_meals(
            plan.id, patient_id, allergens, conditions, restrictions, selected_favourites,
            num_weeks=num_weeks, progress_callback=progress_callback,
            ethnicity=ethnicity, dietary_preference=dietary_preference,
        )
        for meal in meals:
            self.db.add(DietPlanMeal(**meal))
        plan.status = "draft"
        plan.generation_metadata = {
            **plan.generation_metadata,
            "meal_count": len(meals),
            "recipe_url_coverage": round(sum(1 for meal in meals if meal.get("recipe_url")) / len(meals), 2),
        }
        await log(
            self.db,
            doctor_id=patient.doctor_id,
            patient_id=patient_id,
            event_type=AuditEvent.diet_plan_generation_completed,
            metadata={"plan_id": str(plan.id), "meal_count": len(meals)},
        )
        await self.db.flush()
        return await self.get_plan(plan.id, patient.doctor_id)

    async def get_plan(self, plan_id: uuid.UUID, doctor_id: uuid.UUID | None = None) -> DietPlan:
        query = select(DietPlan).where(DietPlan.id == plan_id).options(selectinload(DietPlan.meals))
        if doctor_id is not None:
            query = query.where(DietPlan.doctor_id == doctor_id)
        plan = (await self.db.execute(query)).scalar_one_or_none()
        if plan is None:
            raise ValueError("Diet plan not found")
        return plan

    async def update_serving_multiplier(self, plan_id: uuid.UUID, meal_id: uuid.UUID, doctor_id: uuid.UUID, multiplier: float) -> DietPlanMeal:
        await self.get_plan(plan_id, doctor_id)
        meal = await self.db.get(DietPlanMeal, meal_id)
        if meal is None or meal.diet_plan_id != plan_id:
            raise ValueError("Meal not found")
        meal.serving_multiplier = multiplier
        await self.db.flush()
        return meal

    async def regenerate_meal(self, plan_id: uuid.UUID, meal_id: uuid.UUID, doctor_id: uuid.UUID) -> DietPlanMeal:
        plan = await self.get_plan(plan_id, doctor_id)
        meal = await self.db.get(DietPlanMeal, meal_id)
        if meal is None or meal.diet_plan_id != plan_id:
            raise ValueError("Meal not found")
        profile = await self._get_or_build_profile(plan.patient_id)
        restrictions = self._medical_restrictions(profile.conditions or [], profile.medications or [])
        assigned = [self._meal_to_dict(existing) for existing in plan.meals if existing.week == meal.week and existing.id != meal.id]
        replacement = self._candidate_meal(
            sequence=meal.sequence + _REGEN_OFFSET,
            week=meal.week,
            day=meal.day,
            meal_slot=meal.meal_slot,
            conditions=profile.conditions or [],
            restrictions=restrictions,
            selected_favourites=[],
            suffix="Regenerated",
        )
        replacement = self.recipe_service.enrich(replacement, meal.sequence + _REGEN_OFFSET)
        if not replacement.get("recipe_url"):
            replacement["recipe_url"] = await self.recipe_service.lookup_recipe_url(replacement["meal_name"])
        if self.allergen_service.validate_meal_allergens(replacement, profile.allergens or []):
            replacement = self._fallback_meal(meal.sequence + 997, meal.week, meal.day, meal.meal_slot, conditions=profile.conditions or [])
        if self.no_repeat_service.validate_no_repeats(replacement, assigned):
            replacement["meal_name"] = f"Fresh {meal.meal_slot} Plate {meal.sequence}"

        for key in [
            "meal_name", "base_calories", "base_protein_g", "base_fat_g", "base_carbs_g",
            "ingredients", "recipe_url", "clinical_note",
        ]:
            setattr(meal, key, replacement[key])
        meal.serving_multiplier = 1.0
        await log(
            self.db,
            doctor_id=doctor_id,
            patient_id=plan.patient_id,
            event_type=AuditEvent.meal_regenerated,
            metadata={"plan_id": str(plan_id), "meal_id": str(meal_id)},
        )
        await self.db.flush()
        return meal

    async def regenerate_plan(self, plan_id: uuid.UUID, doctor_id: uuid.UUID) -> DietPlan:
        plan = await self.get_plan(plan_id, doctor_id)
        await self.db.execute(delete(DietPlanMeal).where(DietPlanMeal.diet_plan_id == plan_id))
        profile = await self._get_or_build_profile(plan.patient_id)
        restrictions = self._medical_restrictions(profile.conditions or [], profile.medications or [])
        meals = await self._build_meals(plan.id, plan.patient_id, profile.allergens or [], profile.conditions or [], restrictions, plan.selected_favourites or [])
        for meal in meals:
            self.db.add(DietPlanMeal(**meal))
        plan.status = "draft"
        plan.updated_at = datetime.now(UTC)
        await self.db.flush()
        return await self.get_plan(plan.id, doctor_id)

    async def regenerate_day(self, plan_id: uuid.UUID, doctor_id: uuid.UUID, week: int, day: int) -> DietPlan:
        plan = await self.get_plan(plan_id, doctor_id)
        target_ids = [meal.id for meal in plan.meals if meal.week == week and meal.day == day]
        for meal_id in target_ids:
            await self.regenerate_meal(plan_id, meal_id, doctor_id)
        return await self.get_plan(plan_id, doctor_id)

    async def approve_plan(self, plan_id: uuid.UUID, doctor_id: uuid.UUID) -> DietPlan:
        plan = await self.get_plan(plan_id, doctor_id)
        plan.status = "approved"
        plan.approved_at = datetime.now(UTC)
        await log(
            self.db,
            doctor_id=doctor_id,
            patient_id=plan.patient_id,
            event_type=AuditEvent.plan_approved,
            metadata={"plan_id": str(plan.id)},
        )
        await self.db.flush()
        return plan

    async def _build_meals(
        self,
        plan_id: uuid.UUID,
        patient_id: uuid.UUID,
        allergens: list[str],
        conditions: list[str],
        restrictions: list[str],
        selected_favourites: list[str],
        num_weeks: int = 4,
        progress_callback: Callable[[int, int], None] | None = None,
        ethnicity: str | None = None,
        dietary_preference: str | None = None,
    ) -> list[dict]:
        meals: list[dict] = []
        sequence = 0
        total = num_weeks * 7 * len(MEAL_SLOTS)
        completed = 0
        for week in range(1, num_weeks + 1):
            assigned_this_week: list[dict] = []
            for day in range(1, 8):
                for meal_slot in MEAL_SLOTS:
                    meal = None
                    for attempt in range(3):
                        candidate = await self._generate_candidate_meal(
                            sequence + attempt,
                            week,
                            day,
                            meal_slot,
                            conditions,
                            allergens,
                            restrictions,
                            selected_favourites,
                            assigned_this_week,
                            ethnicity=ethnicity,
                            dietary_preference=dietary_preference,
                        )
                        allergen_violations = self.allergen_service.validate_meal_allergens(candidate, allergens + restrictions)
                        repeat_violations = self.no_repeat_service.validate_no_repeats(candidate, assigned_this_week)
                        if not allergen_violations and not repeat_violations:
                            meal = candidate
                            break
                    if meal is None:
                        meal = self._fallback_meal(sequence, week, day, meal_slot, conditions)
                    assigned_this_week.append(meal)
                    meals.append(
                        {
                            **meal,
                            "diet_plan_id": plan_id,
                            "patient_id": patient_id,
                            "week": week,
                            "day": day,
                            "meal_slot": meal_slot,
                            "sequence": sequence,
                            "serving_multiplier": 1.0,
                        }
                    )
                    sequence += 1
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)
        return meals

    def _candidate_meal(
        self,
        sequence: int,
        week: int,
        day: int,
        meal_slot: str,
        conditions: list[str],
        restrictions: list[str],
        selected_favourites: list[str],
        suffix: str | None = None,
    ) -> dict:
        base = BASE_DISHES[sequence % len(BASE_DISHES)]
        favourite = selected_favourites[sequence % len(selected_favourites)] if selected_favourites and sequence % 9 == 0 else None
        condition_note = self._clinical_note(conditions, restrictions)
        name_parts = [f"Week {week}", meal_slot, favourite or base]
        if suffix:
            name_parts.append(suffix)
        return {
            "meal_name": " ".join(name_parts),
            "clinical_note": condition_note,
            "recipe_url": None,
        }

    async def _generate_candidate_meal(
        self,
        sequence: int,
        week: int,
        day: int,
        meal_slot: str,
        conditions: list[str],
        allergens: list[str],
        restrictions: list[str],
        selected_favourites: list[str],
        assigned_this_week: list[dict],
        ethnicity: str | None = None,
        dietary_preference: str | None = None,
    ) -> dict:
        if self.openai_diet_service.is_enabled():
            try:
                meal = await self.openai_diet_service.generate_meal(
                    week=week,
                    day=day,
                    meal_slot=meal_slot,
                    conditions=conditions,
                    allergens=self.allergen_service.expand_allergens(allergens),
                    restrictions=restrictions,
                    selected_favourites=selected_favourites,
                    assigned_meals_this_week=[assigned["meal_name"] for assigned in assigned_this_week],
                    ethnicity=ethnicity,
                    dietary_preference=dietary_preference,
                )
                return self._ensure_meal_complete(meal, sequence)
            except Exception:
                # If the live model call fails, generation still completes through the guarded fallback path.
                pass
        candidate = self._candidate_meal(sequence, week, day, meal_slot, conditions, restrictions, selected_favourites)
        enriched = self.recipe_service.enrich(candidate, sequence)
        if not enriched.get("recipe_url"):
            enriched["recipe_url"] = await self.recipe_service.lookup_recipe_url(enriched["meal_name"])
        return enriched

    def _ensure_meal_complete(self, meal: dict, sequence: int) -> dict:
        if not meal.get("ingredients") or not meal.get("recipe_url"):
            enriched = self.recipe_service.enrich(meal, sequence)
            return {**enriched, **{key: value for key, value in meal.items() if value not in (None, [], "")}}
        return meal

    def _fallback_meal(self, sequence: int, week: int, day: int, meal_slot: str, conditions: list[str]) -> dict:
        return self.recipe_service.enrich(
            {
                "meal_name": f"Week {week} {meal_slot} Safe Quinoa Plate {day}-{sequence}",
                "clinical_note": self._clinical_note(conditions, ["fallback allergen-safe meal"]),
                "recipe_url": None,
                "recipe_steps": None,
            },
            sequence,
        )

    def _match_condition_rule(self, condition: str) -> dict:
        """Fuzzy match a condition string against condition_rules keys."""
        c = condition.lower().strip()
        if c in self.condition_rules:
            return self.condition_rules[c]
        for key in self.condition_rules:
            if key in c or c in key:
                return self.condition_rules[key]
        return {}

    def _medical_restrictions(self, conditions: list[str], medications: list[str]) -> list[str]:
        restrictions: list[str] = []
        for condition in conditions:
            rule = self._match_condition_rule(condition)
            restrictions.extend(rule.get("avoid", []))
            restrictions.extend(rule.get("limit", []))
        for medication in medications:
            lowered = medication.lower()
            for key, rule in self.medication_rules.items():
                if key in lowered:
                    restrictions.extend(rule.get("avoid", []))
                    restrictions.extend(rule.get("limit", []))
        return self._unique(restrictions)

    async def _get_or_build_profile(self, patient_id: uuid.UUID) -> MedicalProfile:
        profile = await self.db.scalar(select(MedicalProfile).where(MedicalProfile.patient_id == patient_id))
        if profile is not None:
            return profile
        return await MedicalProfileService(self.db).build_medical_profile(patient_id)

    def _clinical_note(self, conditions: list[str], restrictions: list[str]) -> str:
        notes: list[str] = []
        if "hypertension" in conditions:
            notes.append("low sodium")
        if "type 2 diabetes" in conditions or "diabetes" in conditions:
            notes.append("steady carbohydrate distribution")
        if "hypothyroid" in conditions:
            notes.append("soy avoided")
        if "grapefruit" in restrictions:
            notes.append("no grapefruit")
        return "; ".join(self._unique(notes)) or "balanced clinical meal"

    def _load_json(self, filename: str) -> dict:
        path = Path(__file__).resolve().parents[1] / "prompts" / filename
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = value.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    def _meal_to_dict(self, meal: DietPlanMeal) -> dict:
        return {
            "meal_name": meal.meal_name,
            "ingredients": meal.ingredients,
            "week": meal.week,
            "day": meal.day,
            "meal_slot": meal.meal_slot,
        }
