import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.patient import AuditLog, Doctor

router = APIRouter(tags=["audit"])


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID | None
    action: str
    metadata_json: dict | None
    created_at: datetime


@router.get("/api/patients/{patient_id}/audit-logs", response_model=list[AuditLogRead])
@limiter.limit("60/minute")
async def patient_audit_logs(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.doctor_id == doctor.id, AuditLog.patient_id == patient_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    return list(result.scalars())


@router.get("/api/audit-logs", response_model=list[AuditLogRead])
@limiter.limit("60/minute")
async def all_audit_logs(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog).where(AuditLog.doctor_id == doctor.id).order_by(AuditLog.created_at.desc()).limit(200)
    )
    return list(result.scalars())
