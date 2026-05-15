import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.patient import (
    Doctor,
    Patient,
    PatientAllergen,
    PatientCondition,
    PatientFamilyHistory,
    PatientFavouriteFood,
    PatientMedication,
)
from schemas.patient import PatientCreate, PatientListItem, PatientRead, PatientUpdate

router = APIRouter(prefix="/api/patients", tags=["patients"])

CHILDREN = {
    "conditions": PatientCondition,
    "medications": PatientMedication,
    "allergens": PatientAllergen,
    "family_history": PatientFamilyHistory,
    "favourite_foods": PatientFavouriteFood,
}


async def _get_patient_or_404(db: AsyncSession, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Patient:
    result = await db.execute(
        select(Patient)
        .where(Patient.id == patient_id, Patient.doctor_id == doctor_id, Patient.deleted_at.is_(None))
        .options(
            selectinload(Patient.conditions),
            selectinload(Patient.medications),
            selectinload(Patient.allergens),
            selectinload(Patient.family_history),
            selectinload(Patient.favourite_foods),
            selectinload(Patient.documents),
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


async def _next_patient_code(db: AsyncSession, doctor_id: uuid.UUID) -> str:
    year = datetime.now(UTC).year
    count = await db.scalar(select(func.count(Patient.id)).where(Patient.doctor_id == doctor_id))
    return f"PAT-{year}{(count or 0) + 1:04d}"


def _replace_children(patient: Patient, payload: PatientCreate | PatientUpdate) -> None:
    for field, model in CHILDREN.items():
        value = getattr(payload, field, None)
        if value is not None:
            setattr(patient, field, [model(**item.model_dump()) for item in value])


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_patient(
    request: Request,
    payload: PatientCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    data = payload.model_dump(exclude={"conditions", "medications", "allergens", "family_history", "favourite_foods"})
    patient = Patient(**data, doctor_id=doctor.id, patient_code=await _next_patient_code(db, doctor.id))
    _replace_children(patient, payload)
    db.add(patient)
    await db.commit()
    return await _get_patient_or_404(db, doctor.id, patient.id)


@router.get("", response_model=list[PatientListItem])
@limiter.limit("60/minute")
async def list_patients(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[Patient]:
    result = await db.execute(
        select(Patient)
        .where(Patient.doctor_id == doctor.id, Patient.deleted_at.is_(None))
        .order_by(Patient.created_at.desc())
    )
    return list(result.scalars())


@router.get("/{patient_id}", response_model=PatientRead)
@limiter.limit("60/minute")
async def get_patient(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    return await _get_patient_or_404(db, doctor.id, patient_id)


@router.put("/{patient_id}", response_model=PatientRead)
@limiter.limit("30/minute")
async def update_patient(
    request: Request,
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    patient = await _get_patient_or_404(db, doctor.id, patient_id)
    for key, value in payload.model_dump(exclude_unset=True, exclude=set(CHILDREN)).items():
        setattr(patient, key, value)
    _replace_children(patient, payload)
    await db.commit()
    return await _get_patient_or_404(db, doctor.id, patient.id)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_patient(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> None:
    patient = await _get_patient_or_404(db, doctor.id, patient_id)
    patient.deleted_at = datetime.now(UTC)
    await db.commit()
