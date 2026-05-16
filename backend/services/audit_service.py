import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.patient import AuditEvent, AuditLog


async def log(
    db: AsyncSession,
    *,
    doctor_id: uuid.UUID,
    patient_id: uuid.UUID | None,
    event_type: AuditEvent,
    metadata: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        doctor_id=doctor_id,
        patient_id=patient_id,
        action=event_type,
        metadata_json=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry
