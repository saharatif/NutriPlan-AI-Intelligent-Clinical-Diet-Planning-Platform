import asyncio
import uuid
from functools import partial

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_doctor
from api.rate_limit import limiter
from db.database import get_db
from db.supabase_client import get_supabase_client
from models.patient import Doctor, Patient, PatientDocument
from schemas.patient import DocumentRead
from utils.config import settings

router = APIRouter(prefix="/api/patients/{patient_id}/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


async def _assert_patient_owner(db: AsyncSession, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> None:
    exists = await db.scalar(
        select(Patient.id).where(
            Patient.id == patient_id,
            Patient.doctor_id == doctor_id,
            Patient.deleted_at.is_(None),
        )
    )
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> PatientDocument:
    await _assert_patient_owner(db, doctor.id, patient_id)

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF uploads are supported",
        )

    content = await file.read()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    storage_path = f"{doctor.id}/{patient_id}/{uuid.uuid4()}-{file.filename}"

    # Run the synchronous Supabase SDK call in a thread so it does not block the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            get_supabase_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload,
            storage_path,
            content,
            {"content-type": file.content_type},
        ),
    )

    document = PatientDocument(
        patient_id=patient_id,
        file_name=file.filename or "document.pdf",
        storage_path=storage_path,
        content_type=file.content_type or "application/pdf",
        size_bytes=len(content),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=list[DocumentRead])
@limiter.limit("60/minute")
async def list_documents(
    request: Request,
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> list[PatientDocument]:
    await _assert_patient_owner(db, doctor.id, patient_id)
    result = await db.execute(
        select(PatientDocument)
        .where(PatientDocument.patient_id == patient_id)
        .order_by(PatientDocument.uploaded_at.desc())
    )
    return list(result.scalars())
