import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.patient import AuditEvent, Doctor
from services.audit_service import log
from services.diet_plan_service import DietPlanService
from services.pdf_export_service import PdfExportService

router = APIRouter(prefix="/api/diet-plans/{plan_id}", tags=["export"])


@router.post("/export/pdf")
@limiter.limit("10/minute")
async def export_pdf(
    request: Request,
    plan_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        plan = await DietPlanService(db).get_plan(plan_id, doctor.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet plan not found")
    result = await PdfExportService(db).export_plan_pdf(plan)
    await log(db, doctor_id=doctor.id, patient_id=plan.patient_id, event_type=AuditEvent.pdf_exported, metadata={"plan_id": str(plan.id)})
    await db.commit()
    return result


@router.get("/download")
async def download_pdf(plan_id: uuid.UUID, storage_path: str | None = None) -> RedirectResponse:
    return RedirectResponse(url=storage_path or f"/api/diet-plans/{plan_id}")
