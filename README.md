# NutriPlan AI — Intelligent Clinical Diet Planning Platform

A clinical nutrition assistant that lets doctors generate personalised, medically-aware 4-week diet plans for their patients. Doctors log in, upload blood-test PDFs, and the system uses OCR + GPT-4o to produce allergen-safe, condition-aware meal plans that can be reviewed, edited, and exported as a PDF diet chart.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| Backend | Python 3.11 + FastAPI + SQLAlchemy + Alembic + Celery |
| Auth | Supabase Auth (email/password → JWT) |
| Database | Supabase PostgreSQL (RLS enforced on all patient tables) |
| Storage | Supabase Storage (private PDF bucket, signed URLs) |
| Background Jobs | Celery + Redis |
| AI / OCR | OpenAI GPT-4o + Mistral OCR + OpenAI text-embedding-3-small |
| Vector Store | pgvector (default) or Pinecone |
| PDF Export | WeasyPrint |
| Deployment | Docker + Nginx + GitHub Actions + AWS ECS Fargate |

---

## Local Setup

### Prerequisites

- Docker + Docker Compose
- A [Supabase](https://supabase.com) project (free tier works)
- Node.js 20+ (for local frontend dev without Docker)
- Python 3.11+ (for local backend dev without Docker)

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd NutriPlan-AI-Intelligent-Clinical-Diet-Planning-Platform
cp .env.example .env
```

Open `.env` and fill in every value (see Environment Variables below).

### 2. Supabase one-time setup

1. Go to **Project Settings → API** and copy:
   - `Project URL` → `SUPABASE_URL`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`
   - `JWT Secret` → `SUPABASE_JWT_SECRET`
2. Go to **Project Settings → Database → Connection string (URI)** → copy → `DATABASE_URL`
3. Go to **Authentication → Providers → Email** → enable email/password
4. Go to **Storage → New bucket** → name `patient-documents` → set **Private**

### 3. Run the full stack

```bash
docker-compose up --build
```

This starts five services: **nginx** (port 80), **backend** (FastAPI), **celery_worker**, **frontend** (React), **redis**.

- Frontend: [http://localhost](http://localhost)
- API docs: [http://localhost/api/docs](http://localhost/api/docs)
- Health check: [http://localhost/health](http://localhost/health)

### 4. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

Then run the RLS policies from `backend/db/schema.sql` in the Supabase SQL Editor (see Section 5.2 of the project plan).

### 5. Register a doctor account

Go to [http://localhost/login](http://localhost/login) → click **Sign Up** → use your email and a password. Supabase handles the account creation. Your UUID from `auth.users` becomes your `doctors.id`.

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Celery worker

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on [http://localhost:5173](http://localhost:5173) and proxies `/api` to `http://localhost:8000`.

---

## Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --tb=short

# Frontend type check + build
cd frontend
npx tsc --noEmit
npm run build
```

---

## Environment Variables

Copy `.env.example` to `.env`. Never commit `.env`.

```bash
# ── App ──────────────────────────────────────
DEBUG=false

# ── Supabase ─────────────────────────────────
SUPABASE_URL=                        # Project URL from Supabase → Settings → API
SUPABASE_SERVICE_ROLE_KEY=           # service_role key (backend only — never expose to browser)
SUPABASE_JWT_SECRET=                 # JWT Secret (used by FastAPI to verify tokens locally)
DATABASE_URL=                        # PostgreSQL connection string from Supabase → Settings → Database

# ── Redis / Celery ────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── AI Services ──────────────────────────────
OPENAI_API_KEY=
MISTRAL_API_KEY=

# ── Vector Store ─────────────────────────────
VECTOR_BACKEND=pgvector              # "pgvector" (default, free) or "pinecone"
PINECONE_API_KEY=                    # Only needed if VECTOR_BACKEND=pinecone
PINECONE_INDEX_NAME=nutriplan-patients
```

> `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` are **backend-only secrets**. They must never appear in frontend code or browser network requests.

---

## How Doctor Login Works

The browser authenticates **directly with Supabase** — the FastAPI backend is never involved in password verification.

```
Browser → supabase.auth.signInWithPassword({ email, password })
       ← { access_token (JWT), refresh_token }

Browser → GET /api/auth/me
          Authorization: Bearer <access_token>

FastAPI → verifies JWT locally using python-jose + SUPABASE_JWT_SECRET (HS256)
        → extracts sub claim = doctor UUID
        → queries doctors table → returns profile
```

The `SUPABASE_JWT_SECRET` lets FastAPI verify tokens in-process with no network call to Supabase per request.

---

## Project Delivery Plan

See [`agents/plan/`](agents/plan/) for the week-by-week breakdown:

| Week | Focus |
|---|---|
| [Week 1](agents/plan/WEEK_1.md) | Backend foundation + Supabase Auth + patient CRUD + login/dashboard |
| [Week 2](agents/plan/WEEK_2.md) | Mistral OCR + Medical Profile Builder + embeddings |
| [Week 3](agents/plan/WEEK_3.md) | GPT-4o diet plan generation + allergen guard + no-repeat validator |
| [Week 4](agents/plan/WEEK_4.md) | Full React UI + plan review + MacroSlider + PDF export |
| [Week 5](agents/plan/WEEK_5.md) | Docker + Nginx + GitHub Actions CI/CD + AWS ECS Fargate |

---

## Security Rules

- `.env` is in `.gitignore` — verify with `git check-ignore .env`
- `SUPABASE_SERVICE_ROLE_KEY` is used only in the FastAPI backend (server-side)
- `SUPABASE_JWT_SECRET` is used only in the FastAPI backend (server-side)
- The frontend only uses `SUPABASE_URL` and the `anon` key (public, safe)
- Supabase RLS is enabled on all patient tables — a doctor cannot query another doctor's data
- All PDF files are in a private Supabase Storage bucket — access requires a server-generated signed URL
- No patient PII is written to logs — only UUIDs appear in structured log fields
