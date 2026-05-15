import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.patient import Doctor
from utils.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_jwt(token: str) -> dict:
    """Decode and validate a Supabase-issued JWT. Raises 401 on any failure."""
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")


async def get_current_doctor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = _decode_jwt(credentials.credentials)

    try:
        doctor_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        # Doctor has a valid Supabase JWT but has never called POST /api/auth/login.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor profile not found. Call POST /api/auth/login first.",
        )
    return doctor
