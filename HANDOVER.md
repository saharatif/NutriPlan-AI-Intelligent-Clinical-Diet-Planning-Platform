# NutriPlan AI — Developer Handover

**Last updated:** 2026-05-24  
**Project status:** Weeks 1–4 complete. Week 5 (Docker / CI / AWS deployment) not started.

---

## What This Project Is

A clinical nutrition platform where doctors log in, upload blood-test PDFs, and receive AI-generated 4-week personalised diet plans. Plans are allergen-safe, medically aware, and exportable as PDF diet charts.

---

## Handover Checklist for Incoming Developer

- [ ] Read [README.md](README.md) — local setup, env vars, Supabase one-time steps
- [ ] Read [PROGRESS.md](PROGRESS.md) — week-by-week completion status
- [ ] Read [BUGS.md](BUGS.md) — all known bugs (open and resolved)
- [ ] Receive `.env` from the outgoing developer or project lead (never in the repo)
- [ ] Verify `pytest tests/ -v` passes from `backend/` before touching anything
- [ ] Confirm the Supabase project is still active and `GET /health` returns 200

---

## Architecture in One Page

```
Browser
  └── React 18 + TypeScript (Vite / Tailwind / shadcn/ui)
        ↕ /api/* (proxied through Nginx)
FastAPI (Python 3.11) — backend/
  ├── Auth        — Supabase JWT (ES256 or HS256) verified in backend/api/deps.py
  ├── REST API    — backend/api/routes_*.py
  ├── Services    — backend/services/  (OCR, diet plan, allergen, macro, embedding, PDF)
  ├── Workers     — Celery + Redis  (backend/workers/)
  └── DB          — SQLAlchemy async → Supabase PostgreSQL (RLS on all patient tables)

External services:
  Supabase     — auth, PostgreSQL, private PDF storage
  Mistral OCR  — blood-test PDF extraction
  OpenAI       — GPT-4o diet plan generation + text-embedding-3-small
  pgvector     — patient embedding store (Pinecone optional, set VECTOR_BACKEND=pinecone)
```

---

## Key Files to Know First

| File | Why it matters |
|---|---|
| [backend/main.py](backend/main.py) | FastAPI app factory — all routers registered here |
| [backend/utils/config.py](backend/utils/config.py) | All env vars via Pydantic Settings — add new vars here |
| [backend/api/deps.py](backend/api/deps.py) | JWT auth dependency — ES256/HS256 dual support, JWKS cache |
| [backend/utils/clinical_rules.py](backend/utils/clinical_rules.py) | Single source of truth for condition aliases + allergen synonyms |
| [backend/services/diet_plan_service.py](backend/services/diet_plan_service.py) | Core plan generation — allergen guard, no-repeat validator, macro scaling |
| [backend/services/ocr_service.py](backend/services/ocr_service.py) | Mistral OCR + blood marker extraction — BUG-006 is open here |
| [backend/workers/celery_app.py](backend/workers/celery_app.py) | Celery config — task modules registered explicitly (not autodiscover) |
| [alembic/versions/](alembic/versions/) | All DB migrations — run `alembic upgrade head` after pulling |
| [frontend/src/App.tsx](frontend/src/App.tsx) | Route definitions + auth guard |
| [frontend/src/lib/api.ts](frontend/src/lib/api.ts) | Axios singleton with Bearer token interceptor |

---

## Development Process

### Running locally

```bash
# Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install && npm run dev   # http://localhost:5173
```

### Tests

```bash
cd backend
pytest tests/ -v --tb=short   # must be 20+ passing before any PR
```

```bash
cd frontend
npx tsc --noEmit              # zero TypeScript errors required
npm run build
```

### Migrations

After any model change:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Always review the generated file before applying — autogenerate misses some changes (e.g. RLS policies, custom indexes).

### Adding a new API route

1. Create `backend/api/routes_<feature>.py`
2. Register the router in `backend/main.py`
3. Add corresponding service in `backend/services/`
4. Add Pydantic schemas in `backend/schemas/`
5. Write tests in `backend/tests/test_<feature>.py`

---

## Open Bugs

### BUG-006 — OCR misses pipe-delimited table rows (Major, Open)

**File:** `backend/services/ocr_service.py`

Mistral OCR returns structured blood test tables as markdown pipe rows:

```
| ESR | 26 * | mm/hr | ● | 0-20 |
```

The current `MARKER_PATTERN` regex only matches `Marker: value unit` and `Marker = value` formats. Table-format markers (e.g. ESR) are present in raw OCR text but never written to `blood_test_results`.

**Fix needed:** Add a second regex branch in `_parse_blood_markers()` to handle `| name | value | unit | ... |` rows alongside the existing colon/equals pattern.

---

## Resolved Bugs (for context)

| ID | Summary | Root cause |
|---|---|---|
| BUG-005 | Celery tasks not found — KeyError | `autodiscover_tasks` replaced with explicit `include` list in `celery_app.py` |
| BUG-004 | Supabase Storage 400 Bucket not found | `patient-documents` bucket was never created in the dashboard |
| BUG-003 | Doctor login 500 — FK violation on audit_logs | Missing `await db.flush()` before audit log insert in `routes_auth.py` |
| BUG-002 | JWT 401 — Supabase now signs with ES256 | `deps.py` updated to read `alg` header and verify via JWKS for ES256 tokens |
| BUG-001 | Patient wizard accepted only one item per step | `PatientStepForm.tsx` rebuilt with dynamic multi-item lists |

Full details in [BUGS.md](BUGS.md).

---

## What Is NOT Done — Week 5

The entire deployment layer is unbuilt. No Dockerfiles exist for backend or frontend. CI is not configured. AWS is not provisioned. See [agents/plan/WEEK_5.md](agents/plan/WEEK_5.md) for the full spec.

Tasks remaining:

- `backend/Dockerfile` (python:3.11-slim, uvicorn entrypoint)
- `frontend/Dockerfile` (node:20-alpine build → nginx:alpine serve)
- `docker-compose.prod.yml` (ECR image tags, no bind mounts)
- `.github/workflows/ci.yml` (test → build → deploy jobs)
- `infra/cloudformation/template.yml` (ECS Fargate, ALB, Secrets Manager)
- `docs/AWS_DEPLOYMENT.md` (deploy + teardown guide)

---

## Credentials and Secrets

You will need (all go in `.env` — never committed):

| Variable | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role |
| `SUPABASE_JWT_SECRET` | Supabase → Settings → API → JWT secret |
| `DATABASE_URL` | Supabase → Settings → Database → URI |
| `OPENAI_API_KEY` | OpenAI dashboard |
| `MISTRAL_API_KEY` | Mistral console |
| `REDIS_URL` | `redis://redis:6379/0` (local) or Upstash URL (cloud) |
| `PINECONE_API_KEY` | Pinecone console (only if `VECTOR_BACKEND=pinecone`) |

---

## Things That Will Surprise You

- **Supabase JWTs are ES256, not HS256.** The JWT secret in Settings is for HS256 fallback only. New tokens use asymmetric keys fetched from JWKS. `deps.py` handles both — do not simplify this logic.
- **Celery task modules must be listed explicitly.** `autodiscover_tasks` was tried and caused `KeyError`. Keep the explicit `include` list in `celery_app.py`.
- **Mistral OCR requires base64 body, not multipart.** Sending multipart returns 422. `ocr_service.py` sends `document_url` as base64 in JSON — do not change this format.
- **pgvector is the default vector store.** Pinecone is wired and tested but requires `VECTOR_BACKEND=pinecone`. Tests run against the pgvector SQLite fallback — no Pinecone key needed for tests.
- **Diet plan generation has two paths.** Set `DIET_PLAN_GENERATION_PROVIDER=openai` + `OPENAI_API_KEY` for GPT-4o. Without it, the deterministic local generator is used (good for tests, not for production quality).
- **Frontend Node.js broke locally** on the original developer's machine (missing `libicui18n.74.dylib`). Use Docker or a clean Node 20 install.

---

## Contact / References

- Weekly delivery plans: [agents/plan/](agents/plan/)
- Design system: [frontend/DESIGN.md](frontend/DESIGN.md)
- Team roles: [TEAMS/](TEAMS/)
- Bug log: [BUGS.md](BUGS.md)
- Progress tracker: [PROGRESS.md](PROGRESS.md)
