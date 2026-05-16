import asyncio
import uuid

from db.database import AsyncSessionLocal, Base, engine
from models import diet_plan as diet_plan_models  # noqa: F401
from models import medical_profile as medical_profile_models  # noqa: F401
from models import patient as patient_models  # noqa: F401
from models.patient import AuditEvent, AuditLog, Doctor, Patient
from services.audit_service import log


def test_audit_log_records_event_fields() -> None:
    async def _run() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        doctor_id = uuid.uuid4()
        patient_id = uuid.uuid4()
        async with AsyncSessionLocal() as db:
            db.add(Doctor(id=doctor_id, email="doc@example.com", name="Dr Test"))
            db.add(Patient(id=patient_id, doctor_id=doctor_id, patient_code="PAT-20260001", first_name="Mina", last_name="Patel"))
            await db.flush()
            entry = await log(
                db,
                doctor_id=doctor_id,
                patient_id=patient_id,
                event_type=AuditEvent.plan_approved,
                metadata={"plan_id": "abc"},
            )
            await db.commit()
            saved = await db.get(AuditLog, entry.id)
            assert saved is not None
            assert saved.doctor_id == doctor_id
            assert saved.patient_id == patient_id
            assert saved.action == AuditEvent.plan_approved
            assert saved.metadata_json == {"plan_id": "abc"}

    asyncio.run(_run())
