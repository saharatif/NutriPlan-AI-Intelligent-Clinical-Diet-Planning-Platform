import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.diet_plan import DietPlan, DietPlanMeal
from models.patient import Doctor, Patient
from schemas.diet_plan import DietPlanListItem, DietPlanRead, GenerateDietPlanRequest
from services.diet_plan_service import DietPlanService
from services.openai_diet_service import OpenAIDietService
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
) -> dict[str, str | int | None]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    result = AsyncResult(task_id, app=celery_app)
    info = result.info if isinstance(result.info, dict) else {}
    state = result.state
    if state == "PROGRESS":
        status_str = "generating"
        progress = info.get("progress", 0)
    elif state == "SUCCESS":
        status_str = "success"
        progress = 100
    elif state == "FAILURE":
        status_str = "failure"
        progress = 0
    else:
        status_str = state.lower()
        progress = 0
    return {
        "task_id": task_id,
        "status": status_str,
        "plan_id": str(result.result) if result.successful() else None,
        "progress": progress,
    }


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


@router.get("/api/diet-plans")
@limiter.limit("60/minute")
async def list_all_approved_plans(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(
            DietPlan.id,
            DietPlan.patient_id,
            DietPlan.status,
            DietPlan.plan_type,
            DietPlan.approved_at,
            DietPlan.created_at,
            Patient.patient_code,
            Patient.first_name,
            Patient.last_name,
        )
        .join(Patient, Patient.id == DietPlan.patient_id)
        .where(DietPlan.doctor_id == doctor.id, DietPlan.status == "approved")
        .order_by(DietPlan.created_at.desc())
    )
    rows = result.fetchall()
    return [
        {
            "id": str(r.id),
            "patient_id": str(r.patient_id),
            "patient_code": r.patient_code,
            "patient_name": f"{r.first_name} {r.last_name}",
            "status": r.status,
            "plan_type": r.plan_type,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


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


@router.get("/api/diet-plans/{plan_id}/meals/{meal_id}/steps")
@limiter.limit("30/minute")
async def get_meal_steps(
    request: Request,
    plan_id: uuid.UUID,
    meal_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[str]]:
    meal = await db.get(DietPlanMeal, meal_id)
    if meal is None or meal.diet_plan_id != plan_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")

    # Return cached steps if already generated
    if meal.recipe_steps:
        return {"steps": meal.recipe_steps}

    svc = OpenAIDietService()
    if not svc.is_enabled():
        fallback = [
            f"Gather all ingredients: {', '.join(i['name'] for i in (meal.ingredients or []))}.",
            "Prepare and measure each ingredient as listed.",
            "Cook according to standard preparation for this meal type.",
            "Season to taste and serve at appropriate temperature.",
            "Portion as indicated by the serving size.",
        ]
        meal.recipe_steps = fallback
        await db.commit()
        return {"steps": fallback}

    steps = await svc.generate_recipe_steps(meal.meal_name, meal.ingredients or [])
    meal.recipe_steps = steps
    await db.commit()
    return {"steps": steps}
