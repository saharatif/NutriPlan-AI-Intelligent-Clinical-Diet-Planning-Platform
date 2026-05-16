import json
import uuid
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.medical_profile import BloodTestResult, MedicalProfile
from models.patient import AuditEvent, Patient, PatientAllergen, PatientCondition, PatientMedication
from services.audit_service import log
from services.embedding_service import EmbeddingService
from utils.clinical_rules import CONDITION_ALIASES

CONDITION_CONSTRAINTS = {
    "hypertension": {"avoid": [], "limit": ["sodium", "processed foods"], "prefer": ["potassium-rich vegetables", "whole grains"]},
    "type 2 diabetes": {"avoid": ["sugary drinks"], "limit": ["refined carbohydrates"], "prefer": ["high-fiber meals", "lean protein"]},
    "diabetes": {"avoid": ["sugary drinks"], "limit": ["refined carbohydrates"], "prefer": ["high-fiber meals", "lean protein"]},
    "hyperlipidemia": {"avoid": ["trans fats"], "limit": ["saturated fat"], "prefer": ["soluble fiber", "omega-3 rich foods"]},
    "chronic kidney disease": {"avoid": [], "limit": ["sodium", "phosphorus", "potassium"], "prefer": ["renal-friendly protein portions"]},
}

MEDICATION_RULES = {
    "warfarin": "keep vitamin K intake consistent",
    "metformin": "take carbohydrate distribution into account",
    "statin": "limit grapefruit unless clinician approves",
    "levothyroxine": "separate calcium and iron supplements from dosing window",
}


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


class MedicalProfileService:
    def __init__(self, db: AsyncSession, allergen_path: Path | None = None):
        self.db = db
        self.allergen_path = allergen_path or Path(__file__).resolve().parents[2] / "data" / "allergen_synonyms.json"

    def normalise_conditions(self, conditions: list[str]) -> list[str]:
        return _unique([CONDITION_ALIASES.get(condition.strip().lower(), condition.strip().lower()) for condition in conditions])

    def expand_allergen_synonyms(self, allergens: list[str]) -> list[str]:
        synonyms = self._load_allergen_synonyms()
        expanded: list[str] = []
        for allergen in allergens:
            key = allergen.strip().lower()
            expanded.append(key)
            expanded.extend(synonyms.get(key, []))
        return _unique(expanded)

    def resolve_medication_rules(self, medications: list[str]) -> list[str]:
        rules: list[str] = []
        for medication in medications:
            lowered = medication.lower()
            rules.extend(rule for key, rule in MEDICATION_RULES.items() if key in lowered)
        return _unique(rules)

    def build_constraints(self, conditions: list[str], allergens: list[str], medication_rules: list[str]) -> dict[str, list[str]]:
        constraints = {"avoid": list(allergens), "limit": [], "prefer": []}
        for condition in conditions:
            rule = CONDITION_CONSTRAINTS.get(condition, {})
            for bucket in constraints:
                constraints[bucket].extend(rule.get(bucket, []))
        constraints["limit"].extend(medication_rules)
        return {bucket: _unique(values) for bucket, values in constraints.items()}

    async def build_medical_profile(self, patient_id: uuid.UUID) -> MedicalProfile:
        patient = await self.db.get(Patient, patient_id)
        if patient is None:
            raise ValueError("Patient not found")

        conditions = self.normalise_conditions(await self._load_condition_names(patient_id))
        allergens = self.expand_allergen_synonyms(await self._load_allergen_names(patient_id))
        medications = await self._load_medication_names(patient_id)
        abnormal_markers = await self._load_abnormal_marker_names(patient_id)
        medication_rules = self.resolve_medication_rules(medications)
        constraints = self.build_constraints(conditions, allergens, medication_rules)
        embedding_text = self._build_embedding_text(conditions, allergens, medications, abnormal_markers, constraints)

        profile = await self.db.scalar(select(MedicalProfile).where(MedicalProfile.patient_id == patient_id))
        if profile is None:
            profile = MedicalProfile(patient_id=patient_id)
            self.db.add(profile)
        profile.conditions = conditions
        profile.allergens = allergens
        profile.medications = medications
        profile.abnormal_markers = abnormal_markers
        profile.medication_rules = medication_rules
        profile.nutrition_constraints = constraints
        profile.embedding_text = embedding_text

        await EmbeddingService(self.db).update_patient_embedding(
            patient_id,
            embedding_text,
            {"doctor_id": str(patient.doctor_id), "patient_id": str(patient_id), "conditions": conditions},
        )
        await log(
            self.db,
            doctor_id=patient.doctor_id,
            patient_id=patient_id,
            event_type=AuditEvent.medical_profile_built,
            metadata={"conditions": conditions, "allergen_count": len(allergens)},
        )
        await self.db.flush()
        return profile

    async def update_manual_profile(self, patient_id: uuid.UUID, payload: dict) -> MedicalProfile:
        profile = await self.db.scalar(select(MedicalProfile).where(MedicalProfile.patient_id == patient_id))
        if profile is None:
            profile = MedicalProfile(patient_id=patient_id)
            self.db.add(profile)
        for field in ["conditions", "allergens", "medications", "abnormal_markers", "medication_rules", "nutrition_constraints"]:
            if field in payload:
                setattr(profile, field, payload[field])
        profile.embedding_text = self._build_embedding_text(
            profile.conditions,
            profile.allergens,
            profile.medications,
            profile.abnormal_markers,
            profile.nutrition_constraints,
        )
        await EmbeddingService(self.db).update_patient_embedding(
            patient_id,
            profile.embedding_text or "",
            {"patient_id": str(patient_id), "manual_edit": True},
        )
        await self.db.flush()
        return profile

    async def clear_blood_tests_for_document(self, document_id: uuid.UUID) -> None:
        await self.db.execute(delete(BloodTestResult).where(BloodTestResult.document_id == document_id))

    async def _load_condition_names(self, patient_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(select(PatientCondition.name).where(PatientCondition.patient_id == patient_id))
        return list(result.scalars())

    async def _load_allergen_names(self, patient_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(select(PatientAllergen.name).where(PatientAllergen.patient_id == patient_id))
        return list(result.scalars())

    async def _load_medication_names(self, patient_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(select(PatientMedication.name).where(PatientMedication.patient_id == patient_id))
        return list(result.scalars())

    async def _load_abnormal_marker_names(self, patient_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(
            select(BloodTestResult.marker_name).where(BloodTestResult.patient_id == patient_id, BloodTestResult.is_abnormal.is_(True))
        )
        return _unique(list(result.scalars()))

    def _load_allergen_synonyms(self) -> dict[str, list[str]]:
        with self.allergen_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _build_embedding_text(
        self,
        conditions: list[str],
        allergens: list[str],
        medications: list[str],
        abnormal_markers: list[str],
        constraints: dict,
    ) -> str:
        return (
            f"Conditions: {', '.join(conditions)}\n"
            f"Allergens: {', '.join(allergens)}\n"
            f"Medications: {', '.join(medications)}\n"
            f"Abnormal markers: {', '.join(abnormal_markers)}\n"
            f"Nutrition constraints: {json.dumps(constraints, sort_keys=True)}"
        )
