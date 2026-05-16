import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.diet_plan import DietPlan
from models.patient import Doctor, Patient
from schemas.diet_plan import DietPlanListItem, DietPlanRead, GenerateDietPlanRequest
from services.diet_plan_service import DietPlanService
from workers.celery_app import celery_app
from workers.task_diet_plan import generate_diet_plan

router = APIRouter(tags=["diet-plans"])


async def _assert_patient_owner(db: AsyncSession, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Patient:
    patient = await db.get(Patient, patient_id)
    if patient is None or patient.doctor_id != doctor_id or patient.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.post("/api/patients/{patient_id}/diet-plans/generate")
@limiter.limit("10/minute")
async def queue_generation(
    request: Request,
    patient_id: uuid.UUID,
    payload: GenerateDietPlanRequest,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    task = generate_diet_plan.delay(str(patient_id), payload.selected_favourites, payload.plan_type)
    return {"task_id": task.id}


@router.get("/api/patients/{patient_id}/diet-plans/generate/{task_id}/status")
@limiter.limit("60/minute")
async def generation_status(
    request: Request,
    patient_id: uuid.UUID,
    task_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | None]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.state.lower(), "plan_id": str(result.result) if result.successful() else None}


@router.get("/api/patients/{patient_id}/diet-plans", response_model=list[DietPlanListItem])
@limiter.limit("60/minute")
async def list_plans(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[DietPlan]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    result = await db.execute(
        select(DietPlan)
        .where(DietPlan.patient_id == patient_id, DietPlan.doctor_id == doctor.id)
        .order_by(DietPlan.created_at.desc())
    )
    return list(result.scalars())


@router.get("/api/diet-plans/{plan_id}", response_model=DietPlanRead)
@limiter.limit("60/minute")
async def get_plan(
    request: Request,
    plan_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlan:
    try:
        return await DietPlanService(db).get_plan(plan_id, doctor.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet plan not found")


@router.post("/api/diet-plans/{plan_id}/approve", response_model=DietPlanRead)
@limiter.limit("20/minute")
async def approve_plan(
    request: Request,
    plan_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlan:
    try:
        plan = await DietPlanService(db).approve_plan(plan_id, doctor.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet plan not found")
    await db.commit()
    return await DietPlanService(db).get_plan(plan.id, doctor.id)
