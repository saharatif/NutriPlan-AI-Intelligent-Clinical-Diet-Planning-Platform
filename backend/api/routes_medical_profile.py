import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from models.medical_profile import BloodTestResult, MedicalProfile
from models.patient import Doctor, Patient
from schemas.medical_profile import BloodTestResultRead, MedicalProfilePayload, MedicalProfileRead
from services.medical_profile_service import MedicalProfileService

router = APIRouter(prefix="/api/patients/{patient_id}", tags=["medical-profile"])


async def _assert_patient_owner(db: AsyncSession, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Patient:
    patient = await db.get(Patient, patient_id)
    if patient is None or patient.doctor_id != doctor_id or patient.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/blood-tests", response_model=list[BloodTestResultRead])
@limiter.limit("60/minute")
async def blood_tests(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[BloodTestResult]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    result = await db.execute(
        select(BloodTestResult)
        .where(BloodTestResult.patient_id == patient_id)
        .order_by(BloodTestResult.created_at.desc())
    )
    return list(result.scalars())


@router.post("/medical-profile/build", response_model=MedicalProfileRead)
@limiter.limit("20/minute")
async def build_profile(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> MedicalProfile:
    await _assert_patient_owner(db, doctor.id, patient_id)
    profile = await MedicalProfileService(db).build_medical_profile(patient_id)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/medical-profile", response_model=MedicalProfileRead)
@limiter.limit("60/minute")
async def get_profile(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> MedicalProfile:
    await _assert_patient_owner(db, doctor.id, patient_id)
    profile = await db.scalar(select(MedicalProfile).where(MedicalProfile.patient_id == patient_id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical profile not found")
    return profile


@router.put("/medical-profile", response_model=MedicalProfileRead)
@limiter.limit("20/minute")
async def update_profile(
    request: Request,
    patient_id: uuid.UUID,
    payload: MedicalProfilePayload,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> MedicalProfile:
    await _assert_patient_owner(db, doctor.id, patient_id)
    profile = await MedicalProfileService(db).update_manual_profile(patient_id, payload.model_dump())
    await db.commit()
    await db.refresh(profile)
    return profile
