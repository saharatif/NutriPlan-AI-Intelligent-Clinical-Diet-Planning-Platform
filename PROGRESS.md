# NutriPlan AI — Project Progress

## Current Week: 1
## Last Updated: 2026-05-15

---

## Week 1 — Backend Foundation + Frontend Skeleton

**Goal:** `docker-compose up` → log in as a doctor → create a patient → see the dashboard.

### Setup
- [x] Virtual environment created (`backend/.venv`)
- [x] `requirements.txt` created and installed
- [ ] `.env` created from `.env.example` with all values filled
- [ ] Supabase project created; URL, service role key, JWT secret copied
- [ ] Supabase Auth enabled (email/password provider)
- [ ] Supabase Storage bucket `patient-documents` created (private)

### Backend
- [x] `backend/utils/config.py` — Pydantic Settings
- [x] `backend/utils/logging.py` — structlog JSON logger
- [x] `backend/db/database.py` — SQLAlchemy async engine + session
- [x] `backend/db/supabase_client.py` — Supabase Storage + Auth admin client
- [x] `backend/models/patient.py` — ORM models (Doctor, Patient, all sub-tables)
- [x] `backend/schemas/patient.py` — Pydantic v2 schemas
- [x] `backend/api/routes_auth.py` — login, logout, me
- [x] `backend/api/routes_patients.py` — full CRUD
- [x] `backend/api/routes_documents.py` — upload + list
- [x] `backend/api/routes_health.py` — health check
- [x] `backend/api/rate_limit.py` — slowapi limiter
- [x] `backend/workers/celery_app.py` — Celery + Redis wired (no tasks yet)
- [x] `backend/main.py` — FastAPI app factory

### Database
- [x] `alembic.ini` + `alembic/env.py` configured
- [x] `alembic/versions/001_initial_schema.py` — all tables
- [x] `alembic upgrade head` runs cleanly from scratch
- [x] RLS policies applied in Supabase SQL Editor (all 9 tables)

### Frontend
- [ ] `frontend/package.json` + dependencies installed (package file created; local Node binary is broken)
- [x] `frontend/vite.config.ts` + proxy to backend
- [x] `frontend/tailwind.config.js`
- [x] `frontend/src/lib/supabase.ts` — Supabase JS client singleton
- [x] `frontend/src/lib/api.ts` — Axios + Bearer token interceptor
- [x] `frontend/src/store/useAuthStore.ts` — session + doctor profile
- [x] `frontend/src/store/usePatientStore.ts` — patient list + CRUD
- [x] `frontend/src/pages/Login.tsx` — email/password → Supabase Auth
- [x] `frontend/src/pages/Dashboard.tsx` — patient list table
- [x] `frontend/src/pages/NewPatient.tsx` — steps 1–2 only
- [x] `frontend/src/App.tsx` — protected routes + auth guard

### Infrastructure
- [x] `docker-compose.yml` — all 5 services
- [x] `nginx/nginx.conf`
- [x] `.env.example` — all var names, values blank
- [x] `.gitignore` — `.env`, `.venv`, `node_modules`, `dist`

### Acceptance Criteria
- [ ] `docker-compose up` starts all services with no errors
- [x] `GET /health` → HTTP 200 `{status: "ok", version, timestamp}`
- [ ] Doctor registers and logs in via browser; JWT stored in Supabase session
- [x] `GET /api/auth/me` returns doctor profile with valid JWT; 401 without it
- [x] `POST /api/patients` creates patient with all 8 data categories; returns `patient_code`
- [x] `GET /api/patients` returns only the logged-in doctor's patients (RLS verified)
- [x] Second doctor cannot see first doctor's patients (integration test)
- [ ] Invalid fields return HTTP 422 with clean Pydantic error
- [ ] All endpoints return HTTP 429 on rate limit breach
- [ ] PDF uploads to Supabase Storage; document row created in DB
- [x] `pytest tests/test_api.py` passes
- [ ] Login page and dashboard render in browser without console errors

**Status:** Complete

**Session notes (2026-05-15):**
- Added Week 1 backend, Alembic migration, frontend skeleton, Docker Compose, Nginx, and `.env.example`.
- Installed pinned backend dependencies into `backend/.venv`.
- Verified `pytest tests/test_api.py -q` from `backend/` passes: health, auth, patient CRUD, and doctor isolation (`4 passed`, one upstream Supabase deprecation warning).
- Frontend dependency install/build is blocked locally because `/opt/homebrew/Cellar/node/22.7.0/bin/node` cannot load `libicui18n.74.dylib`.

---

## Week 2 — Mistral OCR + Medical Profile Builder + Embeddings

**Goal:** Upload a blood-test PDF → OCR extracts blood markers + allergens → Medical Profile built → patient embedding in vector store.

### Backend
- [ ] `backend/services/ocr_service.py`
- [ ] `backend/services/medical_profile_service.py`
- [ ] `backend/services/embedding_service.py`
- [ ] `backend/services/audit_service.py`
- [ ] `backend/workers/task_ocr.py`
- [ ] `backend/workers/task_medical_profile.py`
- [ ] `backend/api/routes_medical_profile.py`
- [ ] `backend/models/medical_profile.py`
- [ ] `backend/schemas/medical_profile.py`
- [ ] `backend/db/pinecone_client.py`
- [ ] `data/allergen_synonyms.json`

### Frontend
- [ ] `frontend/src/pages/PatientProfile.tsx`
- [ ] `frontend/src/components/OCRResultViewer.tsx`
- [ ] `frontend/src/components/MedicalProfileCard.tsx`
- [ ] `frontend/src/components/AllergenBadge.tsx`

### Acceptance Criteria
- [ ] Celery OCR task processes sample PDF via Mistral OCR
- [ ] Blood markers extracted with correct values, units, `is_abnormal` flags
- [ ] Allergens saved with `source = 'ocr_extracted'`
- [ ] Raw OCR text stored in `ocr_results`
- [ ] Medical Profile normalises conditions + expands allergen synonyms
- [ ] `medical_profiles` upserted after build
- [ ] Patient embedding created in vector store
- [ ] Abnormal blood markers highlighted red in UI
- [ ] Doctor can manually edit medical profile
- [ ] `audit_logs` records `ocr_completed` and `medical_profile_built`
- [ ] `pytest tests/test_ocr_service.py` passes
- [ ] `pytest tests/test_medical_profile_service.py` passes

**Status:** Not Started

---

## Week 3 — Diet Plan Generation Engine

**Goal:** Generate a 112-meal 4-week plan — allergen-safe, no repeats, medically aware, macro-scalable.

### Backend
- [ ] `backend/services/diet_plan_service.py`
- [ ] `backend/services/recipe_service.py`
- [ ] `backend/services/allergen_service.py`
- [ ] `backend/services/no_repeat_service.py`
- [ ] `backend/services/macro_service.py`
- [ ] `backend/workers/task_diet_plan.py`
- [ ] `backend/api/routes_diet_plans.py`
- [ ] `backend/api/routes_meals.py`
- [ ] `backend/models/diet_plan.py`
- [ ] `backend/schemas/diet_plan.py`
- [ ] `backend/prompts/diet_plan_system.txt`
- [ ] `backend/prompts/condition_rules.json`
- [ ] `backend/prompts/medication_rules.json`

### Acceptance Criteria
- [ ] Celery task generates 112-meal plan for test patient
- [ ] Zero allergen violations (including synonyms)
- [ ] Zero dish repeats within any single week (including near-duplicates)
- [ ] Medical condition rules reflected in plan
- [ ] Medication interactions applied
- [ ] Recipe URLs populated for ≥ 60% of meals
- [ ] `PATCH serving_multiplier = 1.5` returns correctly scaled values
- [ ] Single-meal regeneration replaces only the targeted meal
- [ ] `pytest tests/test_allergen_service.py` passes
- [ ] `pytest tests/test_no_repeat_service.py` passes
- [ ] `pytest tests/test_macro_service.py` passes
- [ ] `pytest tests/test_diet_plan_service.py` passes

**Status:** Not Started

---

## Week 4 — Full Frontend UI + Doctor Review + PDF Export

**Goal:** Complete doctor workflow from browser — patient wizard, OCR results, plan review, macro sliders, approve, export PDF.

### Frontend
- [ ] `frontend/src/pages/NewPatient.tsx` — all 7 steps complete
- [ ] `frontend/src/pages/GenerateDietPlan.tsx`
- [ ] `frontend/src/pages/DietPlanReview.tsx`
- [ ] `frontend/src/pages/DietPlan.tsx`
- [ ] `frontend/src/components/Layout.tsx`
- [ ] `frontend/src/components/WeekCalendar.tsx`
- [ ] `frontend/src/components/MealCard.tsx`
- [ ] `frontend/src/components/MealDetailPanel.tsx`
- [ ] `frontend/src/components/MealEditModal.tsx`
- [ ] `frontend/src/components/MacroSlider.tsx`
- [ ] `frontend/src/components/AuditLogTable.tsx`
- [ ] `frontend/src/lib/macroUtils.ts` — `scaleMeal()` pure function

### Backend
- [ ] `backend/services/pdf_export_service.py`
- [ ] `backend/api/routes_export.py`
- [ ] `backend/api/routes_audit.py`
- [ ] `backend/exports/templates/diet_chart.html`

### Acceptance Criteria
- [ ] All 7 steps of New Patient form save correctly
- [ ] OCR status shows Processing → Complete in UI
- [ ] Blood markers highlighted red for abnormal values
- [ ] Generate Plan page: allergic foods blocked from favourite food selector
- [ ] Calendar grid renders on plan completion
- [ ] Click meal → slide-out shows ingredients, clinical_note, recipe link
- [ ] Regenerate single meal → only that cell changes
- [ ] MacroSlider 1.5× updates quantities and macros in real time (no API call)
- [ ] Approve Plan → `status = 'approved'` → redirect to plan view
- [ ] Export PDF → correctly formatted diet chart with allergen banner
- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] `pytest tests/test_audit_service.py` passes

**Status:** Not Started

---

## Week 5 — Docker, Nginx, CI/CD & AWS Deployment

**Goal:** Full stack in Docker, CI green on every push, deployed to AWS ECS Fargate via CloudFormation.

### Infrastructure
- [ ] `backend/Dockerfile`
- [ ] `frontend/Dockerfile`
- [ ] `docker-compose.prod.yml`
- [ ] `.github/workflows/ci.yml`
- [ ] `infra/cloudformation/template.yml`
- [ ] `infra/cloudformation/parameters.dev.json`
- [ ] `docs/AWS_DEPLOYMENT.md`

### Acceptance Criteria
- [ ] `docker-compose up` starts all 5 services without errors
- [ ] Full doctor workflow works through Dockerised stack
- [ ] CI: pytest + TypeScript check + frontend build pass on push to `main`
- [ ] CI: all Docker images build without errors
- [ ] `aws cloudformation deploy` creates the stack without errors
- [ ] App accessible via ALB DNS name
- [ ] CloudWatch logs show structured JSON for all 3 services
- [ ] No secrets in CloudFormation, Docker images, or CI logs
- [ ] `docs/AWS_DEPLOYMENT.md` includes full teardown steps

### Security Checklist
- [ ] `.env` confirmed in `.gitignore`
- [ ] All secrets in AWS Secrets Manager
- [ ] GitHub Actions uses OIDC — no long-lived AWS keys
- [ ] Supabase RLS verified by integration test
- [ ] Nginx security headers: `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`
- [ ] structlog confirmed not logging PII or request bodies
- [ ] Supabase Storage bucket confirmed private

**Status:** Not Started

---

## Blockers

_None currently._

---

## Known Issues

_See [BUGS.md](BUGS.md) for the full bug log._

---

## Notes

- 2026-05-15: Project initialised. Plan finalised in `agents/plan/`. Virtual environment created at `backend/.venv`. Supabase confirmed as auth + database + storage solution.
