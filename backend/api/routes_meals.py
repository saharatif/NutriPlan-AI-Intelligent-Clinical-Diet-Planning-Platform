import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.diet_plan import DietPlan, DietPlanMeal
from models.patient import Doctor
from schemas.diet_plan import DietPlanMealRead, DietPlanRead, ServingMultiplierUpdate
from services.diet_plan_service import DietPlanService

router = APIRouter(prefix="/api/diet-plans/{plan_id}", tags=["meals"])


@router.patch("/meals/{meal_id}", response_model=DietPlanMealRead)
@limiter.limit("30/minute")
async def update_serving_multiplier(
    request: Request,
    plan_id: uuid.UUID,
    meal_id: uuid.UUID,
    payload: ServingMultiplierUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlanMeal:
    try:
        meal = await DietPlanService(db).update_serving_multiplier(plan_id, meal_id, doctor.id, payload.serving_multiplier)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    await db.commit()
    await db.refresh(meal)
    return meal


@router.post("/meals/{meal_id}/regenerate", response_model=DietPlanMealRead)
@limiter.limit("20/minute")
async def regenerate_meal(
    request: Request,
    plan_id: uuid.UUID,
    meal_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlanMeal:
    try:
        meal = await DietPlanService(db).regenerate_meal(plan_id, meal_id, doctor.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    await db.commit()
    await db.refresh(meal)
    return meal


@router.post("/days/{week}/{day}/regenerate", response_model=DietPlanRead)
@limiter.limit("10/minute")
async def regenerate_day(
    request: Request,
    plan_id: uuid.UUID,
    week: int,
    day: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlan:
    try:
        plan = await DietPlanService(db).regenerate_day(plan_id, doctor.id, week, day)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet plan not found")
    await db.commit()
    return await DietPlanService(db).get_plan(plan.id, doctor.id)


@router.post("/regenerate", response_model=DietPlanRead)
@limiter.limit("10/minute")
async def regenerate_plan(
    request: Request,
    plan_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> DietPlan:
    try:
        plan = await DietPlanService(db).regenerate_plan(plan_id, doctor.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diet plan not found")
    await db.commit()
    return await DietPlanService(db).get_plan(plan.id, doctor.id)
