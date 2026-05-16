import uuid
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.patient import Doctor
from utils.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _fetch_jwks() -> list[dict]:
    """Fetch Supabase's public JWKS once and cache it (ES256 verification)."""
    url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("keys", [])


def _decode_jwt(token: str) -> dict:
    """
    Decode a Supabase-issued JWT.  Supabase now signs tokens with ES256 by
    default (newer projects) and HS256 for legacy projects.  We detect the
    algorithm from the token header and verify accordingly.
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")

        if alg == "ES256":
            # New Supabase — verify against the project's public JWKS
            jwks = _fetch_jwks()
            kid = header.get("kid")
            key = next((k for k in jwks if k.get("kid") == kid), jwks[0] if jwks else None)
            if key is None:
                raise JWTError("No matching key in JWKS")
            return jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")
        else:
            # Legacy Supabase — verify with the shared JWT secret (HS256)
            return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid bearer token: {exc}",
        )


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor profile not found. Call POST /api/auth/login first.",
        )
    return doctor
