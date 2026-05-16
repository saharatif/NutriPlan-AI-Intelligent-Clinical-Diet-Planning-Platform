# NutriPlan AI — Project Progress

## Current Week: 4
## Last Updated: 2026-05-16

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
- [x] `backend/services/ocr_service.py`
- [x] `backend/services/medical_profile_service.py`
- [x] `backend/services/embedding_service.py`
- [x] `backend/services/audit_service.py`
- [x] `backend/workers/task_ocr.py`
- [x] `backend/workers/task_medical_profile.py`
- [x] `backend/api/routes_medical_profile.py`
- [x] `backend/models/medical_profile.py`
- [x] `backend/schemas/medical_profile.py`
- [x] `backend/db/pinecone_client.py`
- [x] `data/allergen_synonyms.json`

### Frontend
- [x] `frontend/src/pages/PatientProfile.tsx`
- [x] `frontend/src/components/OCRResultViewer.tsx`
- [x] `frontend/src/components/MedicalProfileCard.tsx`
- [x] `frontend/src/components/AllergenBadge.tsx`

### Acceptance Criteria
- [x] Celery OCR task processes sample PDF via Mistral OCR
- [x] Blood markers extracted with correct values, units, `is_abnormal` flags
- [x] Allergens saved with `source = 'ocr_extracted'`
- [x] Raw OCR text stored in `ocr_results`
- [x] Medical Profile normalises conditions + expands allergen synonyms
- [x] `medical_profiles` upserted after build
- [x] Patient embedding created in vector store
- [x] Abnormal blood markers highlighted red in UI
- [x] Doctor can manually edit medical profile
- [x] `audit_logs` records `ocr_completed` and `medical_profile_built`
- [x] `pytest tests/test_ocr_service.py` passes
- [x] `pytest tests/test_medical_profile_service.py` passes

**Status:** Complete

**Session notes (2026-05-16):**
- Added OCR parsing, medical profile normalisation, allergen synonym expansion, deterministic local embeddings, pgvector-style local vector abstraction, audit logging, Celery OCR/profile tasks, and Week 2 API routes.
- Added `blood_test_results`, `ocr_results`, `medical_profiles`, and `patient_vectors` models plus Alembic migration `002_medical_profile`.
- Added Patient Profile UI, OCR table, Medical Profile card, allergen badges, and dashboard links to profile pages.
- Mistral OCR API call fixed — base64 `document_url` JSON body required (multipart returns 422).
- Chunker integrated into `embedding_service.py` (400-char window, 80-char overlap, newline-snap). Live test on `Sahar_test_reports.pdf` (15 pages → 137 chunks); query "What is Sahar's Ferritin?" returned Ferritin 11.30 ng/mL LOW with score 0.60.
- `pinecone_client.py` upgraded to dual-backend: pgvector (default, works in tests) + real Pinecone SDK with `upsert_document_chunks` / `query_document_chunks` for document-level RAG.
- `task_ocr.py` now calls `embed_and_store_document` after OCR.
- `utils/clinical_rules.py` created — single source of truth for `CONDITION_ALIASES` and `KNOWN_ALLERGENS` (removed duplication between ocr_service and medical_profile_service).
- `audit_service.py` enforces `AuditEvent` enum — raw strings no longer accepted.
- pinecone==5.4.2 added to requirements.txt.
- All 7 tests passing.

---

## Week 3 — Diet Plan Generation Engine

**Goal:** Generate a 112-meal 4-week plan — allergen-safe, no repeats, medically aware, macro-scalable.

### Backend
- [x] `backend/services/diet_plan_service.py`
- [x] `backend/services/recipe_service.py`
- [x] `backend/services/allergen_service.py`
- [x] `backend/services/no_repeat_service.py`
- [x] `backend/services/macro_service.py`
- [x] `backend/workers/task_diet_plan.py`
- [x] `backend/api/routes_diet_plans.py`
- [x] `backend/api/routes_meals.py`
- [x] `backend/models/diet_plan.py`
- [x] `backend/schemas/diet_plan.py`
- [x] `backend/prompts/diet_plan_system.txt`
- [x] `backend/prompts/condition_rules.json`
- [x] `backend/prompts/medication_rules.json`

### Acceptance Criteria
- [x] Celery task generates 112-meal plan for test patient
- [x] Zero allergen violations (including synonyms)
- [x] Zero dish repeats within any single week (including near-duplicates)
- [x] Medical condition rules reflected in plan
- [x] Medication interactions applied
- [x] Recipe URLs populated for ≥ 60% of meals
- [x] `PATCH serving_multiplier = 1.5` returns correctly scaled values
- [x] Single-meal regeneration replaces only the targeted meal
- [x] `pytest tests/test_allergen_service.py` passes
- [x] `pytest tests/test_no_repeat_service.py` passes
- [x] `pytest tests/test_macro_service.py` passes
- [x] `pytest tests/test_diet_plan_service.py` passes

**Status:** Complete

**Session notes (2026-05-16):**
- Added deterministic 112-meal diet plan engine with allergen guard, no-repeat validator, clinical condition and medication restrictions, recipe enrichment, serving multiplier updates, and single/day/full regeneration endpoints.
- Added `diet_plans`, `diet_plan_meals`, and `recipe_library` models plus Alembic migration `003_diet_plan_engine`.
- Added Week 3 prompt and rules files for future GPT-4o integration.
- Added OpenAI JSON-mode meal generation path using `OPENAI_API_KEY`, `OPENAI_DIET_MODEL`, and `DIET_PLAN_GENERATION_PROVIDER=openai`; deterministic generation remains the test fallback.
- Added required Week 3 tests: allergen, no-repeat, macro scaling, and diet plan integration.
- Verified full backend suite from `backend/`: `19 passed`, one upstream Supabase deprecation warning.
- Live GPT-4o generation is not called in tests; app runtime will use OpenAI when credentials are present and provider is `openai`.

---

## Week 4 — Full Frontend UI + Doctor Review + PDF Export

**Goal:** Complete doctor workflow from browser — patient wizard, OCR results, plan review, macro sliders, approve, export PDF.

### Frontend
- [x] `frontend/src/pages/NewPatient.tsx` — all 7 steps complete
- [x] `frontend/src/pages/GenerateDietPlan.tsx`
- [x] `frontend/src/pages/DietPlanReview.tsx`
- [x] `frontend/src/pages/DietPlan.tsx`
- [x] `frontend/src/components/Layout.tsx`
- [x] `frontend/src/components/WeekCalendar.tsx`
- [x] `frontend/src/components/MealCard.tsx`
- [x] `frontend/src/components/MealDetailPanel.tsx`
- [x] `frontend/src/components/MealEditModal.tsx`
- [x] `frontend/src/components/MacroSlider.tsx`
- [x] `frontend/src/components/AuditLogTable.tsx`
- [x] `frontend/src/lib/macroUtils.ts` — `scaleMeal()` pure function

### Backend
- [x] `backend/services/pdf_export_service.py`
- [x] `backend/api/routes_export.py`
- [x] `backend/api/routes_audit.py`
- [x] `backend/exports/templates/diet_chart.html`

### Acceptance Criteria
- [x] All 7 steps of New Patient form save correctly
- [x] OCR status shows Processing → Complete in UI
- [x] Blood markers highlighted red for abnormal values
- [x] Generate Plan page: allergic foods blocked from favourite food selector
- [x] Calendar grid renders on plan completion
- [x] Click meal → slide-out shows ingredients, clinical_note, recipe link
- [x] Regenerate single meal → only that cell changes
- [x] MacroSlider 1.5× updates quantities and macros in real time (no API call)
- [x] Approve Plan → `status = 'approved'` → redirect to plan view
- [x] Export PDF → correctly formatted diet chart with allergen banner
- [x] `npm run build` succeeds with zero TypeScript errors
- [x] `pytest tests/test_audit_service.py` passes

**Status:** Complete

**Session notes (2026-05-16):**
- Added Week 4 backend: audit and PDF export endpoints, `PdfExportService`, diet chart HTML template.
- Added 7-step patient wizard with multi-item dynamic lists per step (conditions, medications, allergens, family history, favourite foods) and drag-and-drop multi-PDF upload.
- `NewPatient.tsx` orchestrates full flow: create patient → upload PDFs → trigger OCR → navigate to profile.
- Generate page now properly polls task status before navigating to review (BUG-001 fix).
- `PatientProfile.tsx` upgraded: Upload PDF button, per-document Process button with polling, file list, plans with status badges, audit log panel.
- Design system overhauled: dark navy sidebar, clinical teal accent, Inter font, professional button radius (8px), slate background, compact typography. `DESIGN.md` rewritten to reflect actual NutriPlan design language.
- `Layout.tsx` upgraded to full sidebar with doctor name, nav icons, active states, sign out.
- `Dashboard.tsx` migrated to use `Layout` component.
- All 20 backend tests passing. TypeScript zero errors.

---

**Post-Week-4 session (2026-05-16) — live testing, auth fixes, Supabase pgvector:**
- BUG-002: Supabase ES256 JWT support added to `deps.py` — reads `alg` header, verifies ES256 via JWKS endpoint, HS256 legacy via shared secret.
- BUG-003: `await db.flush()` added in `routes_auth.py` before audit log insert to resolve FK violation on first login.
- BUG-004: Supabase Storage `patient-documents` bucket created (was missing).
- BUG-005: Celery task discovery fixed — replaced `autodiscover_tasks` with explicit `include` list.
- BUG-006 (Open): OCR regex misses pipe-delimited table format from Mistral. ESR found in raw text (`| ESR | 26 * | mm/hr | ● | 0-20 |`) but not stored to `blood_test_results`.
- Supabase pgvector integrated as primary vector store: migration `003_pgvector` adds native `vector(1536)` column + IVFFlat cosine index. `VectorClient` uses SQL `<=>` operator; dialect-aware SQLite fallback for tests.
- `PatientStepForm` fully rebuilt: multi-item dynamic lists with removable chips, PDF drag-and-drop upload zone.
- Recipe service switched from fake `nutriplan.local` URLs to real TheMealDB API lookups.
- `DESIGN.md` fully replaced with NutriPlan AI's actual design system documentation.
- Live test with Neelam Ashok Bharwani: PDF uploaded to Supabase Storage, Mistral OCR extracted 109 markers, ESR = 26 mm/hr (ABNORMAL, ref 0–20) confirmed from raw OCR text.
- `utils/clinical_rules.py` created as single source of truth for condition aliases and allergen synonyms.
- All 20 backend tests passing throughout.

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
