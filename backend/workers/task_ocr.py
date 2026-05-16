import asyncio
import uuid

from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.supabase_client import get_supabase_client
from models.medical_profile import BloodTestResult, OcrResult
from models.patient import PatientAllergen, PatientCondition, PatientDocument
from models.patient import AuditEvent
from services.audit_service import log
from services.embedding_service import EmbeddingService
from services.medical_profile_service import MedicalProfileService
from services.ocr_service import OcrService
from utils.config import settings
from workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10, name="workers.task_ocr.process_blood_test_pdf")
def process_blood_test_pdf(self, document_id: str) -> str:
    async def _run() -> str:
        async with AsyncSessionLocal() as db:
            document = await db.get(PatientDocument, uuid.UUID(document_id))
            if document is None:
                raise ValueError("Document not found")
            document.ocr_status = "processing"
            await db.commit()
            try:
                pdf_bytes = get_supabase_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(document.storage_path)
                parsed = await OcrService().process_pdf(pdf_bytes)

                await MedicalProfileService(db).clear_blood_tests_for_document(document.id)
                for marker in parsed.blood_markers:
                    db.add(
                        BloodTestResult(
                            patient_id=document.patient_id,
                            document_id=document.id,
                            marker_name=marker.marker_name,
                            value=marker.value,
                            unit=marker.unit,
                            reference_range=marker.reference_range,
                            is_abnormal=marker.is_abnormal,
                            raw_text=marker.raw_text,
                        )
                    )
                db.add(
                    OcrResult(
                        patient_id=document.patient_id,
                        document_id=document.id,
                        raw_text=parsed.raw_text,
                        parsed_json={
                            "allergens": parsed.allergens,
                            "conditions": parsed.conditions,
                            "blood_marker_count": len(parsed.blood_markers),
                        },
                    )
                )
                await _insert_missing_allergens(db, document.patient_id, parsed.allergens)
                await _insert_missing_conditions(db, document.patient_id, parsed.conditions)

                document.ocr_status = "completed"
                document.ocr_processed = True
                document.ocr_error = None
                await log(
                    db,
                    doctor_id=await _doctor_id_for_document(db, document),
                    patient_id=document.patient_id,
                    event_type=AuditEvent.ocr_completed,
                    metadata={"document_id": str(document.id), "markers": len(parsed.blood_markers)},
                )
                # Chunk OCR text and store vectors for document-level RAG retrieval
                chunks_stored = await EmbeddingService(db).embed_and_store_document(
                    document_id=document.id,
                    patient_id=document.patient_id,
                    raw_text=parsed.raw_text,
                )

                await MedicalProfileService(db).build_medical_profile(document.patient_id)
                await db.commit()
                return str(document.id)
            except Exception as exc:
                document.ocr_status = "failed"
                document.ocr_error = str(exc)
                await db.commit()
                raise

    return asyncio.run(_run())


async def _doctor_id_for_document(db, document: PatientDocument):
    from models.patient import Patient

    patient = await db.get(Patient, document.patient_id)
    if patient is None:
        raise ValueError("Patient not found")
    return patient.doctor_id


async def _insert_missing_allergens(db, patient_id: uuid.UUID, allergens: list[str]) -> None:
    existing = set(
        (await db.execute(select(PatientAllergen.name).where(PatientAllergen.patient_id == patient_id))).scalars()
    )
    for allergen in allergens:
        if allergen not in existing:
            db.add(PatientAllergen(patient_id=patient_id, name=allergen, source="ocr_extracted"))


async def _insert_missing_conditions(db, patient_id: uuid.UUID, conditions: list[str]) -> None:
    existing = set(
        (await db.execute(select(PatientCondition.name).where(PatientCondition.patient_id == patient_id))).scalars()
    )
    for condition in conditions:
        if condition not in existing:
            db.add(PatientCondition(patient_id=patient_id, name=condition))
