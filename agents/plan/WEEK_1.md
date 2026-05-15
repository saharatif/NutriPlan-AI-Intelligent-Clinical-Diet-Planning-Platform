# Week 1 — Backend Foundation + Frontend Skeleton

## Goal
A developer can `docker-compose up`, log in as a doctor, create a patient, and see the patient dashboard. No AI features yet — this week is about a solid, tested foundation.

---

## Deliverables

### Backend
| File | Purpose |
|---|---|
| `backend/utils/config.py` | Pydantic Settings — all env vars in one place, no `os.getenv` scattered around |
| `backend/utils/logging.py` | structlog configured for JSON output with request context |
| `backend/db/database.py` | SQLAlchemy async engine + session factory + Base ORM class |
| `backend/db/supabase_client.py` | Supabase Python client (Storage + Auth admin operations) |
| `backend/models/patient.py` | SQLAlchemy ORM models: Doctor, Patient, PatientCondition, PatientMedication, PatientAllergen, PatientFamilyHistory, PatientFavouriteFood, PatientDocument |
| `backend/schemas/patient.py` | Pydantic v2 request/response schemas matching every model above |
| `backend/api/routes_auth.py` | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — JWT dependency injected |
| `backend/api/routes_patients.py` | Full CRUD: `POST`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}` |
| `backend/api/routes_documents.py` | `POST /api/patients/{id}/documents` (upload to Supabase Storage), `GET` list |
| `backend/api/routes_health.py` | `GET /health` → `{status, version, timestamp}` |
| `backend/api/rate_limit.py` | slowapi limiter factory wired to all routes |
| `backend/workers/celery_app.py` | Celery app defined + Redis broker configured (no tasks yet) |
| `backend/main.py` | FastAPI app factory: lifespan, CORS, rate limiter, all routers mounted |
| `backend/requirements.txt` | All pinned dependencies |
| `alembic.ini` + `alembic/env.py` | Async-compatible Alembic config pointing to DATABASE_URL |
| `alembic/versions/001_initial_schema.py` | Migration: all tables from schema.sql |

### Frontend
| File | Purpose |
|---|---|
| `frontend/src/lib/supabase.ts` | Supabase JS client singleton — used for all auth operations |
| `frontend/src/lib/api.ts` | Axios instance with Bearer token interceptor (reads from Supabase session) |
| `frontend/src/store/useAuthStore.ts` | Zustand store: session, doctor profile, login/logout actions |
| `frontend/src/store/usePatientStore.ts` | Zustand store: patient list, selected patient, CRUD actions |
| `frontend/src/pages/Login.tsx` | Email + password form → `supabase.auth.signInWithPassword()` → redirect to Dashboard |
| `frontend/src/pages/Dashboard.tsx` | Patient list table (patient_code, name, created_at) + Add Patient button |
| `frontend/src/pages/NewPatient.tsx` | Steps 1–2 only: Basic Info + Medical Conditions |
| `frontend/src/App.tsx` | React Router v6: protected routes, auth guard, redirect logic |
| `frontend/src/main.tsx` | Entry point |
| `frontend/package.json` | All dependencies pinned |
| `frontend/vite.config.ts` | Vite + React plugin + proxy to backend |
| `frontend/tailwind.config.js` | Tailwind + shadcn/ui content paths |

### Infrastructure
| File | Purpose |
|---|---|
| `docker-compose.yml` | backend + celery_worker + frontend + redis + nginx |
| `nginx/nginx.conf` | `/api/*` → backend:8000, `/` → frontend:80, gzip + security headers |
| `.env.example` | All required env vars, values blank |
| `.gitignore` | `.env`, `__pycache__`, `node_modules`, `.venv`, `dist` |

---

## Supabase Auth Flow (Doctor Login)

```
Browser                     Supabase                    FastAPI Backend
  │                            │                              │
  │── signInWithPassword() ──► │                              │
  │◄── { access_token, ... } ──│                              │
  │    (JWT stored in session)  │                              │
  │                            │                              │
  │── POST /api/auth/login ─────────────────────────────────►│
  │   Authorization: Bearer <access_token>                    │
  │                            │              verify locally  │
  │                            │         python-jose + HS256  │
  │                            │        SUPABASE_JWT_SECRET   │
  │                            │        extract sub → UUID    │
  │                            │         (NO call to Supabase)│
  │◄── { id, name, clinic } ────────────────────────────────-│
```

**JWT Verification (backend):** FastAPI uses `python-jose` to decode the token **locally** using `SUPABASE_JWT_SECRET` (HS256). There is no network call to Supabase per request. The `sub` claim in the decoded payload is the Supabase `auth.users.id`, which is the FK into the `doctors` table.

---

## RLS Policies (run in Supabase SQL Editor after migration)

All 9 policies must be applied. Run this block in full — do not skip any table.

```sql
-- Enable RLS on all patient-facing tables
ALTER TABLE patients                ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_conditions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_medications     ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_allergens       ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_family_history  ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_favourite_foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_documents       ENABLE ROW LEVEL SECURITY;
ALTER TABLE diet_plans              ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs              ENABLE ROW LEVEL SECURITY;

-- Doctors see only their own patients
CREATE POLICY "doctor_owns_patients" ON patients
  FOR ALL USING (doctor_id = auth.uid());

-- Sub-tables are protected via the patients join
CREATE POLICY "doctor_owns_conditions" ON patient_conditions
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_medications" ON patient_medications
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_allergens" ON patient_allergens
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_family_history" ON patient_family_history
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_favourite_foods" ON patient_favourite_foods
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_documents" ON patient_documents
  FOR ALL USING (patient_id IN (SELECT id FROM patients WHERE doctor_id = auth.uid()));

CREATE POLICY "doctor_owns_diet_plans" ON diet_plans
  FOR ALL USING (doctor_id = auth.uid());

CREATE POLICY "doctor_owns_audit_logs" ON audit_logs
  FOR ALL USING (doctor_id = auth.uid());

-- The FastAPI backend connects using the service_role key which bypasses RLS.
-- This is intentional and secure — the service_role key is never sent to the browser.
```

**Verification:** The integration test in `tests/test_api.py` must confirm that doctor B gets an empty list from `GET /api/patients` even when doctor A has patients.

---

## Endpoints This Week

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Service health check |
| POST | `/api/auth/login` | JWT | Log doctor login event, return doctor profile |
| POST | `/api/auth/logout` | JWT | Log logout event |
| GET | `/api/auth/me` | JWT | Return current doctor profile |
| POST | `/api/patients` | JWT | Create patient (all 8 data categories) |
| GET | `/api/patients` | JWT | List this doctor's patients (RLS enforced) |
| GET | `/api/patients/{id}` | JWT | Patient detail |
| PUT | `/api/patients/{id}` | JWT | Update patient |
| DELETE | `/api/patients/{id}` | JWT | Soft-delete (set deleted_at) |
| POST | `/api/patients/{id}/documents` | JWT | Upload PDF to Supabase Storage |
| GET | `/api/patients/{id}/documents` | JWT | List uploaded documents |

---

## Acceptance Criteria

- [ ] `docker-compose up` starts all services — no errors in any container log
- [ ] `GET /health` returns HTTP 200 with `{status: "ok", version, timestamp}`
- [ ] Doctor registers and logs in via browser; JWT stored in Supabase session
- [ ] `GET /api/auth/me` returns doctor name and clinic with valid JWT; 401 without it
- [ ] `POST /api/patients` creates patient with all 8 data categories; returns patient_code (e.g. PAT-20240001)
- [ ] `GET /api/patients` returns only the logged-in doctor's patients (RLS test: second doctor sees empty list)
- [ ] Invalid/missing fields return HTTP 422 with clean Pydantic validation error
- [ ] All endpoints return HTTP 429 after rate limit breach
- [ ] PDF uploads to Supabase Storage `patient-documents` bucket; document row created in DB
- [ ] `alembic upgrade head` runs cleanly from scratch
- [ ] `pytest tests/test_api.py` passes: auth, CRUD, and RLS tests
- [ ] Login page and dashboard render in browser without console errors
- [ ] `README.md` contains local setup instructions, all env vars, and Docker commands
- [ ] `PROGRESS.md` initialised with Week 1 status

---

## Environment Variables Required This Week

```bash
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=
REDIS_URL=redis://redis:6379/0
DEBUG=false
```
