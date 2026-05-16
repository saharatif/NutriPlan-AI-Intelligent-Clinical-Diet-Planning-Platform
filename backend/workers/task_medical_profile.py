import asyncio
import uuid

from db.database import AsyncSessionLocal
from services.medical_profile_service import MedicalProfileService
from workers.celery_app import celery_app


@celery_app.task(name="workers.task_medical_profile.build_medical_profile")
def build_medical_profile(patient_id: str) -> str:
    async def _run() -> str:
        async with AsyncSessionLocal() as db:
            profile = await MedicalProfileService(db).build_medical_profile(uuid.UUID(patient_id))
            await db.commit()
            return str(profile.id)

    return asyncio.run(_run())
