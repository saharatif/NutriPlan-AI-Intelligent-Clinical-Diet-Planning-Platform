import uuid
import asyncio

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from db.database import Base, engine
from main import app
from models import patient  # noqa: F401
from utils.config import settings


def _token(subject: uuid.UUID, email: str = "doctor@example.com") -> str:
    return jwt.encode(
        {"sub": str(subject), "email": email, "aud": "authenticated", "user_metadata": {"name": "Dr Test", "clinic": "Test Clinic"}},
        settings.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture(autouse=True)
def reset_database() -> None:
    async def _reset() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_me_requires_bearer_token() -> None:
    client = TestClient(app)
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_login_creates_doctor_profile_and_me_returns_it() -> None:
    client = TestClient(app)
    doctor_id = uuid.uuid4()
    headers = {"Authorization": f"Bearer {_token(doctor_id)}"}

    # /me must return 401 before the doctor has ever logged in
    assert client.get("/api/auth/me", headers=headers).status_code == 401

    # login creates the doctor row and returns the profile
    login_response = client.post("/api/auth/login", headers=headers)
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["id"] == str(doctor_id)
    assert body["name"] == "Dr Test"
    assert body["clinic"] == "Test Clinic"

    # /me now succeeds
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["id"] == str(doctor_id)


def test_patient_crud_and_doctor_isolation() -> None:
    client = TestClient(app)
    doctor_a = uuid.uuid4()
    doctor_b = uuid.uuid4()

    # Both doctors must log in before they can access any route
    assert client.post("/api/auth/login", headers={"Authorization": f"Bearer {_token(doctor_a, 'a@example.com')}"}).status_code == 200
    assert client.post("/api/auth/login", headers={"Authorization": f"Bearer {_token(doctor_b, 'b@example.com')}"}).status_code == 200

    payload = {
        "first_name": "Mina",
        "last_name": "Patel",
        "sex": "female",
        "height_cm": 164,
        "weight_kg": 68,
        "conditions": [{"name": "Type 2 diabetes"}],
        "medications": [{"name": "Metformin", "dosage": "500mg"}],
        "allergens": [{"name": "Peanuts", "severity": "high"}],
        "family_history": [{"condition": "Hypertension", "relationship": "father"}],
        "favourite_foods": [{"name": "Dal", "preference_level": 5}],
    }

    create_response = client.post("/api/patients", json=payload, headers={"Authorization": f"Bearer {_token(doctor_a, 'a@example.com')}"})
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["patient_code"].startswith("PAT-")
    assert created["conditions"][0]["name"] == "Type 2 diabetes"

    list_a = client.get("/api/patients", headers={"Authorization": f"Bearer {_token(doctor_a, 'a@example.com')}"})
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    list_b = client.get("/api/patients", headers={"Authorization": f"Bearer {_token(doctor_b, 'b@example.com')}"})
    assert list_b.status_code == 200
    assert list_b.json() == []
