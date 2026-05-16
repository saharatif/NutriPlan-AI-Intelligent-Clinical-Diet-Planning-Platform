import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import _decode_jwt, _fetch_jwks, get_current_doctor  # noqa: F401 — _fetch_jwks pre-warms cache on import
from api.rate_limit import limiter
from db.database import get_db
from models.patient import AuditEvent, AuditLog, Doctor
from schemas.patient import DoctorRead

router = APIRouter(prefix="/api/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


@router.post("/login", response_model=DoctorRead)
@limiter.limit("20/minute")
async def login(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """
    Called by the frontend immediately after Supabase sign-in/sign-up.
    Creates the doctor row on first login; updates name/clinic on subsequent logins.
    All other routes require this to have been called at least once.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = _decode_jwt(credentials.credentials)

    try:
        doctor_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    email = str(payload.get("email") or f"{doctor_id}@supabase.local")
    meta = payload.get("user_metadata") or {}
    name = str(meta.get("name") or email.split("@")[0])
    clinic: str | None = meta.get("clinic")

    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        doctor = Doctor(id=doctor_id, email=email, name=name, clinic=clinic)
        db.add(doctor)
    else:
        # Keep profile in sync with Supabase user_metadata on each login
        doctor.name = name
        if clinic:
            doctor.clinic = clinic

    # Flush the doctor row first so the FK constraint on audit_logs is satisfied
    await db.flush()
    db.add(AuditLog(doctor_id=doctor_id, action=AuditEvent.doctor_login))
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.post("/logout")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    db.add(AuditLog(doctor_id=doctor.id, action=AuditEvent.doctor_logout))
    await db.commit()
    return {"status": "ok"}


@router.get("/me", response_model=DoctorRead)
@limiter.limit("60/minute")
async def me(request: Request, doctor: Doctor = Depends(get_current_doctor)) -> Doctor:
    return doctor
