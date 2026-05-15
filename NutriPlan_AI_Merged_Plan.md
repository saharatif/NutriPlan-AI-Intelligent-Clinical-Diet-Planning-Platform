# NutriPlan AI — Intelligent Clinical Diet Planning Platform

## Merged Best-Practice Project Plan · 5-Week Delivery

| Parameter | Value |
|---|---|
| **Project Type** | Healthcare AI / Clinical Nutrition Management System |
| **Timeline** | 5 Weeks (Local → AWS Cloud) |
| **Delivery Model** | Weekly working deliverables with signed-off acceptance criteria |
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + React Hook Form + Zod |
| **Backend** | Python 3.11 + FastAPI + Uvicorn + SQLAlchemy + Pydantic v2 + Alembic |
| **Background Jobs** | Celery + Redis |
| **LLM** | OpenAI GPT-4o (function calling + structured JSON output) |
| **OCR** | Mistral OCR (`mistral-ocr-latest`) |
| **Database** | Supabase PostgreSQL + Supabase Storage + Supabase Auth |
| **ORM / Migrations** | SQLAlchemy + Alembic |
| **Vector Store** | Pinecone (pgvector fallback for < 10,000 patients) |
| **PDF Export** | WeasyPrint (server-side HTML → PDF) |
| **DevOps** | Docker + Nginx + GitHub Actions + AWS ECS Fargate + CloudFormation |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Business Requirement](#2-business-requirement)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Database Schema](#5-database-schema)
6. [AI Workflow Design](#6-ai-workflow-design)
7. [Prompt Engineering Strategy](#7-prompt-engineering-strategy)
8. [Functional Requirements](#8-functional-requirements)
9. [API Endpoints](#9-api-endpoints)
10. [Repository Structure](#10-repository-structure)
11. [Weekly Delivery Plan](#11-weekly-delivery-plan)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Tool Recommendations & Decisions](#13-tool-recommendations--decisions)
14. [PROGRESS.md Instructions](#14-progressmd-instructions)
15. [Final Demo Flow](#15-final-demo-flow)
16. [Production Risks & Mitigations](#16-production-risks--mitigations)
17. [Future Enhancements](#17-future-enhancements)
18. [Delivery Summary](#18-delivery-summary)

---

## 1. Project Overview

NutriPlan AI is a clinical nutrition assistant that empowers dietitians and nutrition doctors to generate personalised, medically-aware 4-week diet plans for their patients. The system:

- Ingests patient data from structured forms and PDF blood-test reports
- Parses PDFs using **Mistral OCR** to extract blood markers, allergens, and conditions
- Normalises all data into a **Medical Profile** (merged manual + OCR data)
- Embeds the medical profile into **Pinecone** for RAG retrieval
- Uses **OpenAI GPT-4o** to generate 4-week meal plans that respect allergens, medical conditions, medications, and nutritional goals
- Enforces allergen safety at both the prompt level and programmatically
- Guarantees no food repeats within a single week
- Supports fully parametrisable macronutrient quantities via a serving-size multiplier
- Allows the doctor to review, edit, and regenerate individual meals before approving the plan
- Saves approved plans to the patient record and exports a formatted PDF diet chart

---

## 2. Business Requirement

A nutrition doctor currently creates weekly diet charts manually. This is time-consuming, error-prone, and does not scale. The system must allow the doctor to:

- Store rich patient profiles covering **8 data categories**: blood tests, allergens, medical conditions, medications (with dosages), anthropometrics (height, weight, BMI, fat/protein index), ethnicity, family history, and 20–25 favourite foods
- Upload PDF blood-test reports and automatically extract structured data via OCR
- Generate 4-week diet plans (Breakfast, Lunch, Snack, Dinner) with calories and macros per meal
- Guarantee **no dish repeats within a single week** (same dish can appear next week with variation)
- **Absolutely exclude allergens** — enforced at the prompt level and programmatically post-generation
- **Adjust serving sizes** via a multiplier (0.5× to 3.0×) that recalculates all ingredient quantities and macros in real time without re-calling the LLM
- **Review, edit, and regenerate** individual meals before approving the plan
- Save the final approved plan to the patient record and download a formatted PDF

---

## 3. High-Level Architecture

```
Doctor opens browser
    │
    ▼
Login Page (React) ──► supabase.auth.signInWithPassword()
    │                        │
    │                        ▼
    │                   Supabase Auth (email / password)
    │                        │
    │◄── { access_token, refresh_token } (JWT stored in Supabase session)
    │
    ▼
All API calls carry: Authorization: Bearer <access_token>
    │
    ▼
FastAPI verifies JWT locally using python-jose + SUPABASE_JWT_SECRET (HS256)
Extracts sub claim → doctor UUID → injected as current_doctor dependency
    │
    ▼
Patient Dashboard
    │
    ├── Patient Profile Form (8 data categories) + PDF Upload
    │
    ▼
Mistral OCR ──► Extract blood markers / allergens / conditions / medications
    │
    ▼
Medical Profile Builder
  (merge manual form data + OCR extraction → normalised patient context)
    │
    ▼
Supabase PostgreSQL  (all patient tables + audit_logs)
Supabase Storage     (PDF files)
    │
    ▼
OpenAI text-embedding-3-small ──► Pinecone Vector Store
                                   (medical profile embeddings per patient)
    │
    ▼
Doctor selects plan type (1-week / 4-week)
Doctor selects 6–7 favourite foods
    │
    ▼
Celery Worker: GPT-4o Diet Plan Generation
    ├── Pinecone RAG: retrieve patient medical context
    ├── condition_rules.json: condition → dietary guidance map
    ├── medication_rules.json: medication → food interaction map
    ├── Recipe Service: recipe_library DB → DuckDuckGo MCP → USDA FoodData Central
    ├── Allergen Guard: HARD prompt constraint + post-gen validator + synonym DB
    └── No-Repeat Validator: per-week uniqueness + Levenshtein near-duplicate check
    │
    ▼
4-Week Draft Plan (112 meals)
    │
    ▼
Doctor Review UI
  ├── Edit individual meal
  ├── Regenerate single meal / full day / full plan
  └── Approve plan
    │
    ▼
Macro Adjustment UI (serving-multiplier sliders — real-time, no API call)
    │
    ▼
Save to Supabase + Audit Log Entry + Export PDF (WeasyPrint)
```

---

## 4. Technology Stack

### 4.1 Frontend

| Technology | Area | Rationale |
|---|---|---|
| React 18 + TypeScript | UI Framework | Type-safe, production-ready |
| Vite | Build Tool | Fast HMR, optimised bundles |
| Tailwind CSS | Styling | Utility-first, responsive |
| shadcn/ui | Component Library | Accessible, headless, composable |
| React Hook Form | Forms | Performance-optimised, uncontrolled inputs |
| Zod | Schema Validation | End-to-end type safety; reuse server schemas |
| React Router v6 | Routing | Protected routes, SPA navigation |
| Zustand | State Management | Lightweight global state |
| Axios | HTTP Client | Auth interceptors, error transforms |
| Recharts | Charts | Macro breakdown charts |
| react-pdf | PDF Preview | Blood-test PDF inline viewer |

### 4.2 Backend

| Technology | Area | Rationale |
|---|---|---|
| Python 3.11+ | Language | |
| FastAPI | API Framework | Async, auto-generates OpenAPI docs |
| Uvicorn | ASGI Server | Production-grade |
| SQLAlchemy 2.0 | ORM | Type-safe queries, easier testing, DB-agnostic |
| Alembic | Migrations | Version-controlled schema evolution |
| Pydantic v2 | Validation | Request / response schemas |
| Celery | Background Jobs | Durable async tasks (OCR, plan generation) |
| Redis | Message Broker + Cache | Celery broker; task status caching |
| Supabase Auth (JWT) | Authentication | Frontend authenticates directly with Supabase; backend verifies JWT locally — no network call to Supabase per request |
| python-jose[cryptography] | JWT Verification | Decodes Supabase JWTs in FastAPI using `SUPABASE_JWT_SECRET` (HS256); extracts `sub` claim as doctor UUID |
| WeasyPrint | PDF Generation | HTML/CSS → PDF server-side |
| slowapi | Rate Limiting | Per-client configurable limits |
| pytest + httpx | Testing | Async-compatible test suite |
| structlog | Logging | Structured JSON logs with context |

### 4.3 AI / ML Services

| Service | Role | Rationale |
|---|---|---|
| OpenAI GPT-4o | Diet Plan Generation | Best instruction-following + function calling |
| Mistral OCR (`mistral-ocr-latest`) | Blood Test PDF Parsing | State-of-the-art structured extraction |
| OpenAI text-embedding-3-small | Patient Context Embeddings | Cost-efficient, high semantic quality |
| Pinecone | Vector Database | Managed, metadata-filtered retrieval per patient |

> **Cost-saving alternative:** `pgvector` (built into Supabase, free) can replace Pinecone for under 10,000 patients. The `VectorStore` service class abstracts the choice — swap with a single config flag (`VECTOR_BACKEND=pgvector|pinecone`).

### 4.4 Data & Storage

| Technology | Role | Notes |
|---|---|---|
| Supabase PostgreSQL | All relational data | RLS on all patient tables |
| Supabase Storage | PDF files | Private bucket; signed URLs for access |
| Redis | Celery broker + task state | Also caches OCR job status |
| Pinecone | Patient embeddings | Namespaced per patient |

### 4.5 External Data Sources

| Service | Purpose | Notes |
|---|---|---|
| DuckDuckGo Search MCP | Recipe discovery | No API key needed; free |
| USDA FoodData Central API | Nutritional ground truth | Free, no key for basic queries |
| Open Food Facts Allergen DB | Allergen synonym taxonomy | Free download; local fuzzy matching |
| Internal `recipe_library` table | Curated recipe database | Seeded at startup; primary recipe source |

> **On AllRecipes MCP:** No official MCP exists. The `recipe_service` first queries the internal `recipe_library`, falls back to DuckDuckGo search + targeted scraping, and grounds all nutritional values against USDA FoodData Central.

### 4.6 DevOps & Deployment

| Area | Technology |
|---|---|
| Containerisation | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| CI/CD | GitHub Actions (OIDC auth to AWS — no long-lived keys) |
| Container Registry | AWS ECR |
| Cloud Runtime | AWS ECS Fargate (Spot tasks for cost reduction) |
| Infrastructure as Code | AWS CloudFormation |
| Logging | AWS CloudWatch |
| Secrets | AWS Secrets Manager (production); `.env` (local) |

---

## 5. Database Schema

All tables enforce **Row Level Security (RLS)**. Doctors access only their own patient data. Every significant action writes to `audit_logs`.

### 5.1 Full Schema

```sql
-- ─────────────────────────────────────────────
-- DOCTORS
-- ─────────────────────────────────────────────
CREATE TABLE doctors (
  id           UUID PRIMARY KEY REFERENCES auth.users(id),
  name         TEXT NOT NULL,
  clinic_name  TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PATIENTS
-- ─────────────────────────────────────────────
CREATE TABLE patients (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doctor_id       UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
  patient_code    TEXT UNIQUE NOT NULL,   -- e.g. PAT-20240001 (auto-generated)
  full_name       TEXT NOT NULL,
  date_of_birth   DATE,
  gender          TEXT,
  ethnicity       TEXT,
  height_cm       NUMERIC,
  weight_kg       NUMERIC,
  bmi             NUMERIC,
  fat_percentage  NUMERIC,
  muscle_index    NUMERIC,
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PATIENT SUB-TABLES
-- ─────────────────────────────────────────────
CREATE TABLE patient_conditions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id     UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  condition_name TEXT NOT NULL,
  severity       TEXT,   -- mild / moderate / severe
  notes          TEXT
);

CREATE TABLE patient_medications (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  medication_name TEXT NOT NULL,
  dosage_mg       NUMERIC,
  frequency       TEXT,   -- e.g. once daily
  notes           TEXT
);

CREATE TABLE patient_allergens (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  allergen   TEXT NOT NULL,
  severity   TEXT,   -- intolerance / allergy / anaphylactic
  source     TEXT    -- 'manual' | 'ocr_extracted'
);

CREATE TABLE patient_family_history (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  condition  TEXT NOT NULL,
  relation   TEXT   -- e.g. father, mother, sibling
);

CREATE TABLE patient_favourite_foods (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id   UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  food_name    TEXT NOT NULL,
  cuisine_type TEXT,
  meal_type    TEXT   -- breakfast / lunch / snack / dinner / any
);

-- ─────────────────────────────────────────────
-- DOCUMENTS & OCR
-- ─────────────────────────────────────────────
CREATE TABLE patient_documents (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id     UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  document_type  TEXT,          -- 'blood_test' | 'diet_chart' | 'other'
  file_name      TEXT,
  storage_path   TEXT,          -- Supabase Storage path
  ocr_processed  BOOLEAN DEFAULT FALSE,
  ocr_job_id     TEXT,          -- Celery task ID for status polling
  uploaded_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ocr_results (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id  UUID NOT NULL REFERENCES patient_documents(id) ON DELETE CASCADE,
  patient_id   UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  raw_text     TEXT,            -- full extracted text (for audit)
  extracted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blood_test_results (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  document_id     UUID REFERENCES patient_documents(id),
  test_date       DATE,
  marker_name     TEXT NOT NULL,   -- e.g. TSH, HbA1c, LDL
  value           NUMERIC,
  unit            TEXT,
  reference_min   NUMERIC,
  reference_max   NUMERIC,
  is_abnormal     BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- MEDICAL PROFILE  (normalised, merged view)
-- ─────────────────────────────────────────────
CREATE TABLE medical_profiles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id            UUID UNIQUE NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  conditions            JSONB,   -- normalised condition names
  allergens             JSONB,   -- merged from manual + OCR; includes synonyms
  medications           JSONB,   -- [{name, dose, frequency, interactions}]
  nutrition_constraints JSONB,   -- {avoid:[], limit:[], prefer:[]}
  abnormal_markers      JSONB,   -- [{name, value, unit, direction}]
  embedding_updated_at  TIMESTAMPTZ,
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- RECIPE LIBRARY  (curated, seeded at startup)
-- ─────────────────────────────────────────────
CREATE TABLE recipe_library (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL,
  cuisine_type TEXT,
  meal_type    TEXT,    -- breakfast / lunch / snack / dinner
  ingredients  JSONB,   -- [{name, quantity, unit, calories, protein_g, fat_g, carbs_g}]
  total_calories   INTEGER,
  total_protein_g  NUMERIC,
  total_fat_g      NUMERIC,
  total_carbs_g    NUMERIC,
  allergens_present JSONB,  -- list of allergen flags for fast filtering
  source_url   TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- DIET PLANS
-- ─────────────────────────────────────────────
CREATE TABLE diet_plans (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id       UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  doctor_id        UUID NOT NULL REFERENCES doctors(id),
  plan_type        TEXT,        -- '1_week' | '4_week'
  total_weeks      INTEGER DEFAULT 4,
  status           TEXT DEFAULT 'draft',  -- draft | under_review | approved | archived
  generation_job_id TEXT,       -- Celery task ID
  llm_model_used   TEXT,
  allergens_excluded JSONB,     -- snapshot of allergens used during generation
  constraints_applied JSONB,   -- snapshot of rules applied
  notes            TEXT,
  generated_at     TIMESTAMPTZ DEFAULT NOW(),
  approved_at      TIMESTAMPTZ,
  pdf_url          TEXT         -- Supabase Storage path after export
);

CREATE TABLE diet_plan_meals (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  diet_plan_id       UUID NOT NULL REFERENCES diet_plans(id) ON DELETE CASCADE,
  week_number        INTEGER NOT NULL,      -- 1–4
  day_of_week        TEXT NOT NULL,         -- Monday–Sunday
  meal_type          TEXT NOT NULL,         -- Breakfast | Lunch | Snack | Dinner
  meal_name          TEXT NOT NULL,
  recipe_id          UUID REFERENCES recipe_library(id),
  recipe_source_url  TEXT,
  ingredients        JSONB NOT NULL,        -- [{name, quantity, unit, calories, protein_g, fat_g, carbs_g}]
  base_calories      INTEGER,
  base_protein_g     NUMERIC,
  base_fat_g         NUMERIC,
  base_carbs_g       NUMERIC,
  serving_multiplier NUMERIC DEFAULT 1.0,  -- doctor-adjustable; macros scale proportionally
  preparation_notes  TEXT,
  is_doctor_edited   BOOLEAN DEFAULT FALSE,
  edit_reason        TEXT
);

-- ─────────────────────────────────────────────
-- AUDIT LOGS
-- ─────────────────────────────────────────────
CREATE TABLE audit_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doctor_id   UUID REFERENCES doctors(id),
  patient_id  UUID REFERENCES patients(id),
  event_type  TEXT NOT NULL,   -- see Event Types below
  entity_id   UUID,            -- ID of the affected record
  metadata    JSONB,           -- event-specific detail
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Audit event types:
-- doctor_login | patient_created | patient_updated
-- document_uploaded | ocr_completed | medical_profile_built
-- diet_plan_generation_started | diet_plan_generation_completed
-- meal_regenerated | plan_approved | pdf_exported
-- allergen_violation_detected | no_repeat_violation_detected
```

### 5.2 Row Level Security (RLS) Policies

Run these in the Supabase SQL Editor immediately after the Alembic migration. They ensure a doctor can never query another doctor's patients — even if a backend bug produces the wrong `doctor_id`.

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

-- Service role key (used by the FastAPI backend) bypasses RLS — this is intentional
-- and secure because the service role key is never exposed to the browser
```

> **Verification test:** After enabling RLS, the integration test suite creates two doctor accounts and confirms that `GET /api/patients` for doctor B returns an empty list even when doctor A has patients. This test must pass before Week 1 is considered complete.

---

### 5.3 Serving Multiplier — Implementation Design

The `serving_multiplier` column stores the doctor's chosen scaling factor. The `ingredients` JSONB column stores all values **at base serving (multiplier = 1.0)**. All scaling is computed **client-side in real time** — no API call on slider change.

```json
// Row in diet_plan_meals at base serving:
{
  "meal_name": "Scrambled Eggs with Whole Wheat Toast",
  "base_calories": 394,
  "base_protein_g": 25,
  "base_fat_g": 15,
  "base_carbs_g": 41,
  "serving_multiplier": 1.0,
  "ingredients": [
    { "name": "eggs",             "quantity": 2,   "unit": "large",  "calories": 140, "protein_g": 12, "fat_g": 10, "carbs_g": 1  },
    { "name": "whole wheat bread","quantity": 2,   "unit": "slices", "calories": 160, "protein_g": 6,  "fat_g": 2,  "carbs_g": 30 },
    { "name": "semi-skimmed milk","quantity": 200, "unit": "ml",     "calories": 94,  "protein_g": 7,  "fat_g": 3,  "carbs_g": 10 }
  ]
}
```

```typescript
// macroUtils.ts — pure function, no API call, runs on every slider tick
export function scaleMeal(meal: Meal, multiplier: number): ScaledMeal {
  return {
    ...meal,
    serving_multiplier:  multiplier,
    effective_calories:  Math.round(meal.base_calories  * multiplier),
    effective_protein_g: +(meal.base_protein_g * multiplier).toFixed(1),
    effective_fat_g:     +(meal.base_fat_g     * multiplier).toFixed(1),
    effective_carbs_g:   +(meal.base_carbs_g   * multiplier).toFixed(1),
    ingredients: meal.ingredients.map(ing => ({
      ...ing,
      quantity: +(ing.quantity * multiplier).toFixed(1),
    })),
  };
}
// Slider: 0.5× to 3.0× in 0.25 steps
// Example: 2 eggs at 1.5× → 3 eggs; 394 kcal → 591 kcal; 25g protein → 37.5g
```

---

## 6. AI Workflow Design

### 6.1 Medical Extraction Workflow (Celery Task)

```
PDF Upload to Supabase Storage
    │
    ▼
Celery Task: process_blood_test_pdf(document_id)
    │
    ├── Download PDF from Supabase Storage
    ├── Call Mistral OCR API (mistral-ocr-latest)
    ├── Parse structured response
    ├── Extract blood markers → save to blood_test_results
    │     (is_abnormal = True where value outside reference range)
    ├── Extract allergen mentions → save to patient_allergens (source='ocr_extracted')
    ├── Extract condition mentions → save to patient_conditions (source='ocr_extracted')
    ├── Save raw OCR text → ocr_results (for audit)
    ├── Call Medical Profile Builder
    └── Mark document as ocr_processed=True
    │
    ▼
Medical Profile Builder: build_medical_profile(patient_id)
    │
    ├── Load all patient sub-tables (conditions, medications, allergens, etc.)
    ├── Merge manual + OCR-extracted data
    ├── Normalise condition names (e.g. "thyroid" → "hypothyroidism")
    ├── Expand allergen synonyms (e.g. "milk" → includes whey, casein, lactose)
    ├── Resolve medication food interactions from medication_rules.json
    ├── Build nutrition_constraints: { avoid:[], limit:[], prefer:[] }
    ├── Upsert medical_profiles table
    └── Trigger: update_patient_embedding(patient_id)
    │
    ▼
Embedding Service: update_patient_embedding(patient_id)
    │
    ├── Build embedding text from medical profile
    └── Upsert into Pinecone (namespace: "patients", id: "patient_{uuid}")
```

### 6.2 Diet Plan Generation Workflow (Celery Task)

```
POST /diet-plans/generate  →  Celery task queued  →  return {task_id}
    │
    ▼
Celery Task: generate_diet_plan(patient_id, selected_favourites, plan_type)
    │
    ├── Load patient + medical_profile from Supabase
    ├── Retrieve patient embedding context from Pinecone (RAG)
    ├── Load condition_rules.json + medication_rules.json
    ├── Build dietary rule strings for this patient
    ├── Compile HARD allergen list (manual + ocr_extracted + synonyms)
    ├── Query recipe_library for suitable base recipes
    ├── Build system prompt from template (see Section 7)
    │
    ├── For each week (1–4):
    │     assigned_meals_this_week = []
    │     For each day (Mon–Sun):
    │       For each meal slot (Breakfast, Lunch, Snack, Dinner):
    │         Call GPT-4o (function calling, JSON schema)
    │         → allergen_guard.validate(meal, allergens)
    │             if violation → regenerate (max 3 retries) → log to audit_logs
    │         → no_repeat_service.validate(meal, assigned_meals_this_week)
    │             if duplicate → regenerate (max 3 retries) → log to audit_logs
    │         → recipe_service.enrich(meal)  [USDA macro grounding]
    │         → append to assigned_meals_this_week
    │
    ├── Persist draft plan to diet_plans + diet_plan_meals
    ├── Write audit_log: diet_plan_generation_completed
    └── Update task status → "completed"
```

---

## 7. Prompt Engineering Strategy

### 7.1 System Prompt Template (`backend/prompts/diet_plan_system.txt`)

```
SYSTEM ROLE:
You are a clinical nutritionist AI assistant. You generate medically-safe,
personalised meal plans in strict compliance with all constraints below.
You never override medical or allergen rules, even if a favourite food conflicts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATIENT SUMMARY (from Pinecone RAG):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{patient_medical_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HARD CONSTRAINTS — NEVER VIOLATE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The following allergens MUST NOT appear in any meal in any form —
including hidden ingredients, sauces, dressings, or cross-contamination risk:
  {allergen_list}

Treat all synonyms and derivatives as equivalent:
  - "milk allergy" → also blocks: dairy, cream, butter, ghee, whey, casein, lactose
  - "oat allergy"  → also blocks: oatmeal, granola, oat flour, oat milk, muesli
  - "peanut allergy" → also blocks: groundnuts, peanut butter, satay sauce
If a favourite food contains an allergen, exclude it silently without mentioning it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEDICAL DIETARY RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{condition_rules_for_this_patient}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEDICATION FOOD INTERACTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{medication_rules_for_this_patient}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREFERENCES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Patient ethnicity: {ethnicity}
Incorporate culturally appropriate dishes where possible.
Favourite foods to include this week (use where medically safe):
  {selected_favourites}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NO-REPEAT CONSTRAINT (CRITICAL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dishes already assigned this week:
  {assigned_meals_this_week}
Do NOT use any of these dishes by name or close variation.
A different preparation of the same base (e.g. pasta) is allowed ONLY if
the preparation is substantially different (e.g. "Chicken Pasta" vs "Pasta Primavera").

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT SCHEMA (strict JSON only, no prose):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return a single JSON object matching this schema:
{
  "meal_name": string,
  "meal_type": string,
  "recipe_source": string | null,
  "clinical_note": string | null,   // explain why any food was excluded or chosen
  "ingredients": [
    {
      "name": string,
      "quantity": number,
      "unit": string,
      "calories": number,
      "protein_g": number,
      "fat_g": number,
      "carbs_g": number
    }
  ],
  "base_calories": number,
  "base_protein_g": number,
  "base_fat_g": number,
  "base_carbs_g": number
}
```

### 7.2 Medical Condition Rules (`condition_rules.json`)

```json
{
  "hypothyroidism": {
    "include": ["iodine-rich fish", "eggs", "dairy", "seaweed", "selenium-rich Brazil nuts"],
    "exclude": ["soy products", "raw cruciferous vegetables in large quantities", "millet"],
    "note": "Cooking cruciferous vegetables reduces goitrogens — small amounts of cooked broccoli are fine."
  },
  "hypertension": {
    "include": ["banana", "avocado", "sweet potato", "oats", "fatty fish", "berries"],
    "exclude": ["high-sodium processed foods", "cured meats", "excessive red meat"],
    "sodium_limit_mg": 1500
  },
  "type_2_diabetes": {
    "include": ["low-GI foods", "legumes", "whole grains", "lean protein", "non-starchy vegetables"],
    "exclude": ["refined sugars", "white bread", "sugary drinks", "large portions of white rice"],
    "note": "Spread carbohydrates evenly across all four meal slots."
  },
  "high_cholesterol": {
    "include": ["oats", "lentils", "fatty fish (omega-3)", "nuts", "olive oil"],
    "exclude": ["trans fats", "excessive saturated fat", "full-fat dairy in large quantities"]
  },
  "anaemia": {
    "include": ["red meat", "lentils", "spinach", "tofu", "vitamin C sources to aid iron absorption"],
    "exclude": ["tea and coffee with meals — inhibits iron absorption", "calcium supplements at same time as iron-rich meals"]
  },
  "kidney_disease": {
    "include": ["low-potassium vegetables", "white bread over whole grain", "lean protein in moderate quantities"],
    "exclude": ["high-potassium foods (banana, potato, tomato in large quantities)", "high-phosphorus foods", "excess protein"],
    "note": "Flag all high-protein meals for doctor review."
  },
  "vitamin_d_deficiency": {
    "include": ["oily fish (salmon, mackerel)", "egg yolks", "fortified dairy or plant milk", "mushrooms"],
    "exclude": []
  }
}
```

### 7.3 Medication Food Interactions (`medication_rules.json`)

```json
{
  "thyroxine": {
    "timing_notes": "Taken on empty stomach. Avoid the following within 4 hours of dose.",
    "exclude_near_dose": ["soy products", "high-fibre foods", "calcium-rich foods", "coffee"],
    "note": "If patient takes thyroxine at breakfast, avoid calcium-rich breakfast items."
  },
  "metformin": {
    "include": ["high-fibre foods", "complex carbohydrates"],
    "note": "Always taken with food to reduce GI side effects. Spread carbs evenly."
  },
  "warfarin": {
    "consistency_required": ["leafy green vegetables — vitamin K must be consistent week-to-week, not eliminated"],
    "exclude": ["grapefruit", "cranberry juice in large amounts"],
    "note": "Do not eliminate vitamin K foods; keep intake steady across all weeks."
  },
  "statins": {
    "exclude": ["grapefruit", "grapefruit juice"],
    "include": ["CoQ10-supportive foods: oily fish, nuts, whole grains"]
  },
  "amlodipine": {
    "exclude": ["grapefruit", "grapefruit juice"]
  },
  "iron_supplements": {
    "include": ["vitamin C sources at same meal to enhance absorption"],
    "exclude": ["calcium-rich foods at same meal", "tea and coffee at same meal"]
  }
}
```

### 7.4 Allergen Synonyms (`data/allergen_synonyms.json` — sourced from Open Food Facts)

```json
{
  "milk":     ["dairy", "cream", "butter", "ghee", "whey", "casein", "lactose", "cheese", "yogurt"],
  "eggs":     ["egg white", "egg yolk", "albumin", "mayonnaise"],
  "oats":     ["oatmeal", "granola", "muesli", "oat flour", "oat milk", "porridge"],
  "peanuts":  ["groundnuts", "peanut butter", "satay", "arachis oil"],
  "tree_nuts":["almonds", "cashews", "walnuts", "pecans", "hazelnuts", "pistachios"],
  "wheat":    ["flour", "bread", "pasta", "semolina", "spelt", "gluten"],
  "soy":      ["soya", "tofu", "tempeh", "edamame", "miso", "soy sauce", "tamari"],
  "fish":     ["cod", "salmon", "tuna", "haddock", "tilapia", "anchovies", "fish sauce"],
  "shellfish":["shrimp", "prawn", "crab", "lobster", "clams", "oysters", "scallops"],
  "sesame":   ["tahini", "sesame oil", "sesame seeds", "hummus"]
}
```

### 7.5 No-Repeat Validation Logic

```python
# no_repeat_service.py
from rapidfuzz import distance

def validate_no_repeats(week_meals: list[dict]) -> list[dict]:
    """
    Returns list of violations (should be empty before persisting).
    Uses Levenshtein distance to catch near-duplicates (e.g. 'Chicken Pasta'
    vs 'Chicken Pasta Bake' would still flag as too similar).
    """
    seen = []
    violations = []
    for meal in week_meals:
        key = meal['meal_name'].lower().strip()
        for prev in seen:
            # Exact match
            if key == prev:
                violations.append({"meal": meal['meal_name'], "reason": "exact_repeat"})
                break
            # Near-duplicate: edit distance < 8 characters
            if distance.Levenshtein.distance(key, prev) < 8:
                violations.append({"meal": meal['meal_name'], "reason": "near_duplicate", "similar_to": prev})
                break
        seen.append(key)
    return violations
```

---

## 8. Functional Requirements

| ID | Requirement | Key Details |
|---|---|---|
| FR-1 | Doctor Authentication | Supabase Auth email/password; JWT on all routes; RLS enforced; auth state persists on refresh |
| FR-2 | Patient Dashboard | Patient list, search, filter, quick stats, navigation to profile and plan generation |
| FR-3 | Patient Profile (Create/Edit) | All 8 data categories; auto-generated `patient_code`; validated via Zod; favourite foods 20–25 items |
| FR-4 | Document Upload | PDF and image (JPG/PNG) upload to Supabase Storage; metadata linked to patient; Celery OCR task queued |
| FR-5 | OCR Processing | Mistral OCR extracts blood markers (with abnormal flags), allergens, conditions, medications; raw text stored |
| FR-6 | Medical Profile Builder | Merges manual + OCR data; normalises condition names; expands allergen synonyms; computes `nutrition_constraints`; upserts `medical_profiles`; triggers embedding update |
| FR-7 | Favourite Food Selection | Doctor selects 6–7 items from patient's saved list; allergic foods are blocked from selection |
| FR-8 | Diet Plan Generation (1-week / 4-week) | Async Celery task; GPT-4o function calling; 4 meals per day; per-meal: ingredients, calories, protein, fat, carbs |
| FR-9 | Allergen Protection Engine | HARD prompt constraint + post-generation validator with synonym DB; violations trigger regeneration (max 3 retries); all violations logged |
| FR-10 | Meal Diversity Engine | No dish repeats within a week; Levenshtein near-duplicate check; cross-week repeats allowed with modification |
| FR-11 | Clinical Rule Engine | `condition_rules.json` + `medication_rules.json` injected into prompt; rules visible in `clinical_note` field per meal |
| FR-12 | Macro Parametrisation | `serving_multiplier` (0.5× to 3.0×); client-side real-time calculation via `scaleMeal()`; PATCH endpoint persists final multiplier |
| FR-13 | Doctor Review & Edit | View draft plan; edit individual meal; regenerate single meal / full day / full plan; meals marked `is_doctor_edited = TRUE` with reason |
| FR-14 | Plan Approval | Doctor explicitly approves plan; `status` → `approved`; `approved_at` timestamp; audit log entry |
| FR-15 | Save Diet Plan | Approved plan saved to `diet_plans` + `diet_plan_meals`; snapshot of allergens and constraints stored |
| FR-16 | PDF Export | WeasyPrint renders HTML template → PDF; includes patient details, week-by-week grid, macros, allergen warnings, doctor notes; stored in Supabase Storage |
| FR-17 | Audit Logging | All key events written to `audit_logs` with `doctor_id`, `patient_id`, `event_type`, `metadata` |
| FR-18 | Health Check | `GET /health` → HTTP 200 + service metadata; used by Docker and ALB health checks |
| FR-19 | Rate Limiting | `slowapi` per-client limits on all public endpoints; HTTP 429 with clean error on breach |

---

## 9. API Endpoints

### Health
```http
GET /health
```

### Auth

> **Important:** The browser authenticates directly with Supabase (not through the FastAPI backend). The backend auth routes exist for logging, profile fetching, and session lifecycle — not for password verification.

```http
POST /api/auth/login    # Logs the doctor_login audit event; returns doctor profile row
POST /api/auth/logout   # Logs the doctor_logout audit event
GET  /api/auth/me       # Returns current doctor's profile using the JWT sub claim
```

All three routes require `Authorization: Bearer <supabase_jwt>`. The JWT is issued by Supabase and verified by FastAPI locally using `python-jose` — no round-trip to Supabase on each request.

### Patients
```http
POST   /api/patients
GET    /api/patients
GET    /api/patients/{id}
PUT    /api/patients/{id}
DELETE /api/patients/{id}
```

### Documents & OCR
```http
POST /api/patients/{id}/documents
GET  /api/patients/{id}/documents
POST /api/patients/{id}/documents/{doc_id}/process
GET  /api/patients/{id}/documents/{doc_id}/status
GET  /api/patients/{id}/blood-tests
```

### Medical Profile
```http
POST /api/patients/{id}/medical-profile/build
GET  /api/patients/{id}/medical-profile
PUT  /api/patients/{id}/medical-profile
```

### Diet Plans
```http
POST /api/patients/{id}/diet-plans/generate
GET  /api/patients/{id}/diet-plans/generate/{task_id}/status
GET  /api/patients/{id}/diet-plans
GET  /api/diet-plans/{plan_id}
POST /api/diet-plans/{plan_id}/approve
```

### Meal Editing
```http
PATCH  /api/diet-plans/{plan_id}/meals/{meal_id}
POST   /api/diet-plans/{plan_id}/meals/{meal_id}/regenerate
POST   /api/diet-plans/{plan_id}/days/{week}/{day}/regenerate
POST   /api/diet-plans/{plan_id}/regenerate
```

### Export
```http
POST /api/diet-plans/{plan_id}/export/pdf
GET  /api/diet-plans/{plan_id}/download
```

### Audit
```http
GET /api/patients/{id}/audit-logs
GET /api/audit-logs
```

---

## 10. Repository Structure

```
nutriplan-ai/
│
├── README.md
├── PROGRESS.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .dockerignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── main.py
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/               # migration files
│   │
│   ├── api/
│   │   ├── routes_auth.py
│   │   ├── routes_patients.py
│   │   ├── routes_documents.py
│   │   ├── routes_medical_profile.py
│   │   ├── routes_diet_plans.py
│   │   ├── routes_meals.py
│   │   ├── routes_export.py
│   │   ├── routes_audit.py
│   │   ├── routes_health.py
│   │   └── rate_limit.py
│   │
│   ├── workers/
│   │   ├── celery_app.py           # Celery app definition + Redis broker
│   │   ├── task_ocr.py             # process_blood_test_pdf task
│   │   ├── task_medical_profile.py # build_medical_profile task
│   │   └── task_diet_plan.py       # generate_diet_plan task
│   │
│   ├── services/
│   │   ├── ocr_service.py          # Mistral OCR integration
│   │   ├── medical_profile_service.py  # normalisation + constraint builder
│   │   ├── embedding_service.py    # OpenAI embeddings → Pinecone
│   │   ├── diet_plan_service.py    # GPT-4o generation orchestrator
│   │   ├── recipe_service.py       # recipe_library → DuckDuckGo → USDA
│   │   ├── allergen_service.py     # guard + synonym expansion
│   │   ├── no_repeat_service.py    # weekly uniqueness + Levenshtein
│   │   ├── macro_service.py        # serving multiplier + daily totals
│   │   ├── pdf_export_service.py   # WeasyPrint diet chart
│   │   └── audit_service.py        # write to audit_logs
│   │
│   ├── models/
│   │   ├── patient.py              # SQLAlchemy ORM models
│   │   ├── diet_plan.py
│   │   ├── medical_profile.py
│   │   ├── recipe.py
│   │   └── audit.py
│   │
│   ├── schemas/
│   │   ├── patient.py              # Pydantic v2 request/response schemas
│   │   ├── diet_plan.py
│   │   ├── medical_profile.py
│   │   └── audit.py
│   │
│   ├── db/
│   │   ├── database.py             # SQLAlchemy engine + session
│   │   ├── supabase_client.py      # Supabase Storage + Auth client
│   │   ├── pinecone_client.py      # Pinecone / pgvector abstraction
│   │   └── schema.sql              # reference only (Alembic manages migrations)
│   │
│   ├── prompts/
│   │   ├── diet_plan_system.txt    # GPT-4o system prompt template
│   │   ├── condition_rules.json    # medical condition → dietary rules
│   │   └── medication_rules.json  # medication → food interaction rules
│   │
│   ├── exports/
│   │   └── templates/
│   │       └── diet_chart.html     # WeasyPrint HTML template
│   │
│   └── utils/
│       ├── config.py               # settings from environment variables
│       ├── logging.py              # structlog JSON logger
│       └── validators.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── store/
│       │   ├── usePatientStore.ts
│       │   └── useDietPlanStore.ts
│       ├── lib/
│       │   ├── api.ts              # Axios client + auth interceptor
│       │   ├── macroUtils.ts       # scaleMeal() — client-side multiplier
│       │   ├── supabase.ts         # Supabase client for auth state
│       │   └── utils.ts
│       ├── types/
│       │   └── index.ts
│       ├── schemas/
│       │   └── patient.ts          # Zod schemas (shared with backend shapes)
│       ├── components/
│       │   ├── Layout.tsx
│       │   ├── PatientCard.tsx
│       │   ├── MealCard.tsx
│       │   ├── MacroSlider.tsx     # 0.5× to 3.0× with live macro display
│       │   ├── AllergenBadge.tsx   # colour-coded by severity
│       │   ├── WeekCalendar.tsx    # 7-day × 4-meal grid
│       │   ├── MealDetailPanel.tsx # slide-out: ingredients, slider, recipe link
│       │   ├── MealEditModal.tsx   # inline edit + regenerate single meal
│       │   ├── PatientStepForm.tsx # 7-step wizard (RHF + Zod)
│       │   ├── OCRResultViewer.tsx # blood test marker table
│       │   ├── MedicalProfileCard.tsx
│       │   ├── AuditLogTable.tsx
│       │   └── ui/                 # shadcn/ui components
│       └── pages/
│           ├── Login.tsx
│           ├── Dashboard.tsx
│           ├── NewPatient.tsx
│           ├── PatientProfile.tsx
│           ├── GenerateDietPlan.tsx
│           ├── DietPlanReview.tsx  # doctor review + edit + approve
│           └── DietPlan.tsx        # approved plan view + macro sliders
│
├── tests/
│   ├── test_api.py
│   ├── test_ocr_service.py
│   ├── test_medical_profile_service.py
│   ├── test_allergen_service.py
│   ├── test_no_repeat_service.py
│   ├── test_macro_service.py
│   ├── test_diet_plan_service.py
│   └── test_audit_service.py
│
├── data/
│   ├── sample_patient.json
│   ├── sample_blood_report.pdf     # used in automated OCR tests
│   ├── sample_recipes.json         # seed data for recipe_library
│   ├── allergen_synonyms.json      # Open Food Facts taxonomy
│   └── clinical_rules_test.json   # eval cases for rule engine
│
├── nginx/
│   └── nginx.conf
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── PROMPTS.md
│   ├── AWS_DEPLOYMENT.md
│   └── DEMO_SCRIPT.md
│
├── infra/
│   └── cloudformation/
│       ├── template.yml
│       └── parameters.dev.json
│
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 11. Weekly Delivery Plan

> **Rule:** A week is not complete until ALL acceptance criteria are verified. PROGRESS.md must be updated at the end of every session.

---

### 🔵 WEEK 1 — Backend Foundation + Frontend Skeleton

#### Rationale for This Split

Week 1 does **not** try to build everything. The backend is the foundation everything else depends on — it must be solid before OCR, AI, or frontend work begins. The frontend skeleton (login + dashboard shell) is included so there is something visual to show, but all complex UI is deferred to Week 4.

#### Required Working Outcome

By end of Week 1, a developer can:
- Start the full stack with a single `docker-compose up`
- Log in as a doctor through the browser
- Create a patient with all 8 data categories via API
- See the patient list on the dashboard (even if unstyled)
- Upload a medical PDF (file is stored; OCR not yet wired)
- Run the automated test suite and see it pass

#### Backend Components

```
backend/main.py
backend/api/routes_auth.py
backend/api/routes_patients.py
backend/api/routes_documents.py   (upload only — no OCR yet)
backend/api/routes_health.py
backend/api/rate_limit.py
backend/models/patient.py
backend/schemas/patient.py
backend/db/database.py            (SQLAlchemy engine + session)
backend/db/supabase_client.py     (Storage + Auth client)
backend/utils/config.py
backend/utils/logging.py          (structlog JSON)
backend/workers/celery_app.py     (wired but no tasks yet)
alembic/                          (initial migration: all tables)
docker-compose.yml                (backend + redis + nginx + frontend)
.env.example
requirements.txt
```

#### Frontend Components

```
frontend/src/pages/Login.tsx        (fully working Supabase Auth flow)
frontend/src/pages/Dashboard.tsx    (patient list with patient_code + name)
frontend/src/pages/NewPatient.tsx   (steps 1–2 only: basic info + conditions)
frontend/src/lib/api.ts
frontend/src/lib/supabase.ts
frontend/src/store/usePatientStore.ts
```

#### Endpoints

| Endpoint | Description |
|---|---|
| `GET  /health` | HTTP 200 + service metadata |
| `POST /api/auth/login` | Doctor login → Supabase JWT |
| `POST /api/auth/logout` | Invalidate session |
| `GET  /api/auth/me` | Current doctor profile |
| `POST /api/patients` | Create patient (all 8 data categories) |
| `GET  /api/patients` | List doctor's patients (RLS enforced) |
| `GET  /api/patients/{id}` | Patient detail |
| `PUT  /api/patients/{id}` | Update patient |
| `POST /api/patients/{id}/documents` | Upload PDF to Supabase Storage |
| `GET  /api/patients/{id}/documents` | List uploaded documents |

#### Supabase Setup (One-Time)

1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Copy the following from **Project Settings → API**:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_SERVICE_ROLE_KEY` (service_role key — never expose to browser)
   - `SUPABASE_JWT_SECRET` (JWT Secret — used by FastAPI to verify tokens locally)
3. Copy the database connection string from **Project Settings → Database → Connection string (URI)** → set as `DATABASE_URL`.
4. Run initial Alembic migration: `alembic upgrade head` — creates all tables.
5. Run the RLS policy SQL from Section 5.2 in the Supabase SQL Editor.
6. Enable Supabase Auth: **Authentication → Providers → Email** → enable email/password sign-in.
7. Create Storage bucket: **Storage → New bucket** → name `patient-documents` → set to **Private**.
8. Seed `recipe_library` table: `python scripts/seed_recipes.py`.

#### Week 1 Acceptance Criteria

- [ ] `docker-compose up` starts all services without errors (backend, Redis, Nginx, frontend).
- [ ] `GET /health` returns HTTP 200 with service name and version.
- [ ] Doctor can register and log in through the browser; JWT is stored.
- [ ] `POST /api/patients` creates a patient with all 8 data categories.
- [ ] `GET /api/patients` returns only the logged-in doctor's patients — a second doctor cannot see them (RLS verified by integration test).
- [ ] Invalid / missing fields return HTTP 422 with a clean validation error.
- [ ] All endpoints return HTTP 429 on rate-limit breach.
- [ ] PDF uploads to Supabase Storage and document row is created (OCR not triggered yet).
- [ ] Initial Alembic migration runs cleanly (`alembic upgrade head`).
- [ ] `pytest tests/test_api.py` passes with auth, CRUD, and RLS tests.
- [ ] Login page and dashboard are accessible in the browser.
- [ ] `README.md` includes full local setup, environment variables, and Docker instructions.
- [ ] `PROGRESS.md` initialised.

---

### 🟢 WEEK 2 — Mistral OCR + Medical Profile Builder + Embeddings

#### Required Working Outcome

By end of Week 2, a developer can: upload a blood-test PDF, trigger OCR, view structured blood markers (with abnormal flags) in the DB, see allergens auto-populated from the report, see the Medical Profile built and stored, and verify the patient embedding exists in Pinecone.

#### Backend Components

```
backend/workers/task_ocr.py
backend/workers/task_medical_profile.py
backend/services/ocr_service.py
backend/services/medical_profile_service.py
backend/services/embedding_service.py
backend/services/audit_service.py
backend/api/routes_medical_profile.py
backend/models/medical_profile.py
backend/schemas/medical_profile.py
backend/db/pinecone_client.py
tests/test_ocr_service.py
tests/test_medical_profile_service.py
data/sample_blood_report.pdf
data/allergen_synonyms.json
```

#### Frontend Components

```
frontend/src/pages/PatientProfile.tsx     (blood test table + allergen badges)
frontend/src/components/OCRResultViewer.tsx
frontend/src/components/MedicalProfileCard.tsx
frontend/src/components/AllergenBadge.tsx
```

#### Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/patients/{id}/documents/{doc_id}/process` | Queue Celery OCR task |
| `GET  /api/patients/{id}/documents/{doc_id}/status` | Poll task completion |
| `GET  /api/patients/{id}/blood-tests` | Structured markers with `is_abnormal` |
| `POST /api/patients/{id}/medical-profile/build` | Manually trigger profile rebuild |
| `GET  /api/patients/{id}/medical-profile` | Retrieve normalised medical profile |
| `PUT  /api/patients/{id}/medical-profile` | Doctor edits profile |

#### Medical Profile Builder Logic

```python
# medical_profile_service.py
async def build_medical_profile(patient_id: str) -> MedicalProfile:
    # 1. Load all patient sub-tables from DB
    conditions  = await load_conditions(patient_id)   # manual + ocr
    allergens   = await load_allergens(patient_id)    # manual + ocr
    medications = await load_medications(patient_id)
    markers     = await load_abnormal_markers(patient_id)

    # 2. Normalise condition names
    #    "thyroid" → "hypothyroidism", "high bp" → "hypertension"
    conditions  = normalise_conditions(conditions)

    # 3. Expand allergen synonyms from allergen_synonyms.json
    #    "milk" → also blocks [dairy, cream, butter, whey, casein, ...]
    expanded_allergens = expand_allergen_synonyms(allergens)

    # 4. Resolve medication interactions from medication_rules.json
    med_rules = [medication_rules[m.name] for m in medications if m.name in medication_rules]

    # 5. Build nutrition_constraints
    constraints = build_constraints(conditions, expanded_allergens, med_rules)
    # → { avoid: [...], limit: [...], prefer: [...] }

    # 6. Upsert medical_profiles table
    profile = await upsert_medical_profile(patient_id, {
        "conditions": conditions,
        "allergens": expanded_allergens,
        "medications": medications,
        "nutrition_constraints": constraints,
        "abnormal_markers": markers
    })

    # 7. Trigger embedding update
    await embedding_service.update_patient_embedding(patient_id)

    # 8. Write audit log
    await audit_service.log(patient_id, "medical_profile_built", {"conditions": conditions})

    return profile
```

#### Pinecone Embedding Design

```python
# Namespace: "patients"
# Vector ID: "patient_{patient_id}"

metadata = {
    "patient_id":       str(patient.id),
    "doctor_id":        str(patient.doctor_id),
    "patient_code":     patient.patient_code,
    "allergens":        profile.allergens,          # expanded synonyms
    "conditions":       profile.conditions,
    "medications":      [m['name'] for m in profile.medications],
    "bmi_category":     bmi_category(patient.bmi),
    "abnormal_markers": [f"{m['name']}: {m['value']} {m['unit']} ({m['direction']})"
                         for m in profile.abnormal_markers],
    "ethnicity":        patient.ethnicity,
    "updated_at":       datetime.utcnow().isoformat()
}
```

#### Week 2 Acceptance Criteria

- [ ] Celery OCR task processes a sample blood-test PDF using Mistral OCR.
- [ ] Blood markers are extracted and saved to `blood_test_results` with correct values, units, and `is_abnormal` flags.
- [ ] Allergens detected in the PDF are saved to `patient_allergens` with `source = 'ocr_extracted'`.
- [ ] `ocr_results` stores the full raw text for audit.
- [ ] Medical Profile Builder normalises conditions, expands allergen synonyms, and builds `nutrition_constraints`.
- [ ] Medical profile is upserted into `medical_profiles` table.
- [ ] Patient context embedding is created/updated in Pinecone after profile build.
- [ ] Doctor can view blood markers in the patient profile page (abnormal values highlighted in red).
- [ ] Doctor can manually edit the medical profile via the UI.
- [ ] `audit_logs` records `ocr_completed` and `medical_profile_built` events.
- [ ] `pytest tests/test_ocr_service.py` and `tests/test_medical_profile_service.py` pass.
- [ ] `PROGRESS.md` updated.

---

### 🟡 WEEK 3 — Diet Plan Generation Engine

#### Required Working Outcome

By end of Week 3: calling the generation endpoint for a test patient returns a structured 112-meal draft plan; no allergens appear in any meal; no dish repeats within any single week; medical condition and medication rules are reflected in the plan; serving-multiplier scaling works correctly; and all six new tests pass.

#### Backend Components

```
backend/workers/task_diet_plan.py
backend/services/diet_plan_service.py
backend/services/recipe_service.py
backend/services/allergen_service.py
backend/services/no_repeat_service.py
backend/services/macro_service.py
backend/api/routes_diet_plans.py
backend/api/routes_meals.py
backend/models/diet_plan.py
backend/schemas/diet_plan.py
tests/test_diet_plan_service.py
tests/test_allergen_service.py
tests/test_no_repeat_service.py
tests/test_macro_service.py
```

#### Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/patients/{id}/diet-plans/generate` | Queue generation task; returns `{task_id}` |
| `GET  /api/patients/{id}/diet-plans/generate/{task_id}/status` | Poll completion |
| `GET  /api/patients/{id}/diet-plans` | List saved plans |
| `GET  /api/diet-plans/{plan_id}` | Full plan JSON |
| `PATCH /api/diet-plans/{plan_id}/meals/{meal_id}` | Update `serving_multiplier` |
| `POST /api/diet-plans/{plan_id}/meals/{meal_id}/regenerate` | Regenerate one meal |
| `POST /api/diet-plans/{plan_id}/days/{week}/{day}/regenerate` | Regenerate one day |
| `POST /api/diet-plans/{plan_id}/regenerate` | Regenerate full plan |

#### Allergen Guard

```python
# allergen_service.py
import json
from rapidfuzz import fuzz

with open("data/allergen_synonyms.json") as f:
    SYNONYMS = json.load(f)

def expand_allergens(raw_allergens: list[str]) -> list[str]:
    """Expand each allergen to include all known synonyms."""
    expanded = set(raw_allergens)
    for allergen in raw_allergens:
        for canonical, synonyms in SYNONYMS.items():
            if allergen.lower() in [canonical] + synonyms:
                expanded.update([canonical] + synonyms)
    return list(expanded)

def validate_plan_allergens(meals: list[dict], expanded_allergens: list[str]) -> list[dict]:
    """
    Fuzzy-match every ingredient name against the expanded allergen list.
    Fuzzy match catches typos and partial matches (e.g. "oat bran" vs "oats").
    """
    violations = []
    for meal in meals:
        for ing in meal.get('ingredients', []):
            for allergen in expanded_allergens:
                if fuzz.partial_ratio(ing['name'].lower(), allergen.lower()) > 85:
                    violations.append({
                        "meal": meal['meal_name'],
                        "ingredient": ing['name'],
                        "matched_allergen": allergen
                    })
    return violations
```

#### Recipe Service

```python
# recipe_service.py
async def get_recipe(meal_name: str, allergens: list[str]) -> dict | None:
    # 1. Query internal recipe_library (fastest, most reliable)
    recipe = await db.query_recipe_library(meal_name, exclude_allergens=allergens)
    if recipe:
        return recipe

    # 2. DuckDuckGo MCP search: "site:allrecipes.com {meal_name} recipe"
    url = await duckduckgo_search(f"site:allrecipes.com {meal_name} recipe")
    if url:
        ingredients = await scrape_recipe_page(url)
        # Validate no allergens in scraped ingredients
        if not validate_plan_allergens([{"ingredients": ingredients}], allergens):
            return {"recipe_source_url": url, "ingredients": ingredients}

    # 3. USDA FoodData Central: ground calorie + macro values
    return await usda_lookup(meal_name)
```

#### Week 3 Acceptance Criteria

- [ ] Celery task generates a 4-week plan (112 meals) for a test patient.
- [ ] All meals have `meal_name`, `base_calories`, `base_protein_g`, `base_fat_g`, `base_carbs_g`, and a populated `ingredients` JSONB array.
- [ ] No allergens (including synonyms) appear in any meal — verified by `test_allergen_service.py`.
- [ ] No dish repeats within any single week, including near-duplicates — verified by `test_no_repeat_service.py`.
- [ ] The same dish may reappear in a different week with a modified name.
- [ ] Medical condition rules are reflected (e.g. no soy for hypothyroid patient; low sodium for hypertensive).
- [ ] Medication interactions are applied (e.g. no grapefruit for statin patient).
- [ ] Recipe source URLs are populated for ≥ 60% of meals.
- [ ] `PATCH serving_multiplier = 1.5` returns all values correctly scaled (× 1.5).
- [ ] Single-meal regeneration works and replaces only the targeted meal.
- [ ] `audit_logs` records `diet_plan_generation_completed` and any `allergen_violation_detected` events.
- [ ] All six tests pass: `test_diet_plan_service`, `test_allergen_service`, `test_no_repeat_service`, `test_macro_service`.
- [ ] `PROGRESS.md` updated.

---

### 🟠 WEEK 4 — Full Frontend UI + Doctor Review + PDF Export

#### Required Working Outcome

By end of Week 4: a doctor can use the full application from browser — create a patient, upload a blood report, see OCR results, generate a plan, review and edit individual meals, adjust macros with sliders, approve the plan, and download a PDF diet chart.

#### Frontend Pages

| Page (Route) | Description |
|---|---|
| `Login (/login)` | Email + password; Supabase Auth; redirect on success |
| `Dashboard (/)` | Patient list with search + filter; quick stats; Add Patient CTA |
| `New Patient (/patients/new)` | 7-step wizard (React Hook Form + Zod): Basic Info → Conditions → Medications → Allergens → Family History → Favourite Foods (20–25 items) → Documents + Review |
| `Patient Profile (/patients/{id})` | Blood test results (abnormal in red); allergen badges; OCR status; medical profile; saved plans |
| `Generate Plan (/patients/{id}/generate)` | Plan type selector; favourite food selector (6–7 items; allergic foods blocked); async progress with task polling |
| `Plan Review (/diet-plans/{id}/review)` | Draft plan calendar; click meal → edit/regenerate modal; day-level regenerate; Approve button |
| `Diet Plan (/diet-plans/{id})` | Approved plan; week tabs; MacroSlider on each meal; recipe links; Export PDF |

#### New Patient Step Form (7 Steps)

```
Step 1: Basic Info           name, DOB, gender, ethnicity, height, weight, BMI
Step 2: Medical Conditions   condition name, severity, notes
Step 3: Medications          name, dosage_mg, frequency
Step 4: Allergens            allergen, severity (intolerance / allergy / anaphylactic)
Step 5: Family History       condition, relation
Step 6: Favourite Foods      20–25 items with meal-type preference
Step 7: Documents + Review   PDF upload, summary review, Save button
```

On save:
- Toast: "Patient saved! Would you like to generate a diet plan?"
- → "1-Week Plan" or "4-Week Plan"
- 4-Week: opens `GenerateDietPlan` page with favourite food selector

#### Doctor Review Page (`DietPlanReview.tsx`)

```
WeekCalendar grid (read-only, colour-coded by meal type)
│
├── Click any meal cell → MealDetailPanel slide-out:
│     ├── Full ingredient list
│     ├── Calories + macros (base values)
│     ├── "Edit Meal" button → MealEditModal (free-text + regenerate)
│     ├── "Regenerate This Meal" button → POST /meals/{id}/regenerate
│     └── clinical_note (why this meal was chosen / constraints applied)
│
├── "Regenerate Day" button (per day column)
├── "Regenerate Full Plan" button
│
└── "Approve Plan" button (sticky footer)
      → POST /diet-plans/{id}/approve
      → redirect to DietPlan view (with MacroSliders enabled)
```

#### PDF Export Content

```
Page 1: Cover — Patient name, ID, Doctor name, Clinic, Generation date
         Allergen warning banner (bright red border)
         Summary: BMI, Conditions, Total weekly calories

Pages 2–5: One page per week
  ┌─────────────────────────────────────────────────────────────────┐
  │ Week 1         │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │ Sun │
  ├────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  │ Breakfast      │ ... │ ... │ ... │ ... │ ... │ ... │ ... │
  │ Lunch          │ ... │                                     │
  │ Snack          │ ... │                                     │
  │ Dinner         │ ... │                                     │
  └─────────────────────────────────────────────────────────────────┘
  Each cell: meal name + kcal + P/F/C macros

Page 6: Doctor's notes + clinical rules applied
```

#### Week 4 Acceptance Criteria

- [ ] `npm run dev` starts the frontend on `http://localhost:5173` without errors.
- [ ] Doctor can log in; JWT is stored for subsequent API calls.
- [ ] All 7 steps of the New Patient form save correctly; patient appears in dashboard.
- [ ] PDF upload triggers OCR Celery task; OCR status shows "Processing" then "Complete".
- [ ] Blood markers appear in the patient profile (abnormal values highlighted in red).
- [ ] Medical profile is visible and doctor can edit it.
- [ ] Generate Plan page shows favourite food selector (allergic foods blocked from selection).
- [ ] Generation progress polling works; calendar grid renders on completion.
- [ ] Click any meal → slide-out panel shows ingredients, clinical note, recipe link.
- [ ] "Regenerate This Meal" replaces only that meal without affecting the rest of the plan.
- [ ] MacroSlider at 1.5× updates all ingredient quantities and macros in real time (no API call).
- [ ] "Approve Plan" saves plan with `status = 'approved'` and redirects to plan view.
- [ ] Export PDF downloads a correctly formatted diet chart with allergen warnings.
- [ ] `audit_logs` table shows all key events for the session.
- [ ] `npm run build` succeeds with zero TypeScript errors.
- [ ] `PROGRESS.md` updated.

---

### 🟣 WEEK 5 — Docker, Nginx, CI/CD & AWS Deployment

#### Required Working Outcome

By end of Week 5: `docker-compose up` runs the complete stack; CI passes tests and builds images on every push; CloudFormation deploys the application to AWS ECS Fargate; the app is accessible via an Application Load Balancer URL; logs appear in CloudWatch; and all AWS resources can be torn down with a single command.

#### Docker Compose (`docker-compose.yml`)

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80"]
    volumes: ["./nginx/nginx.conf:/etc/nginx/nginx.conf:ro"]
    depends_on: [frontend, backend]

  backend:
    build: { context: ./backend, dockerfile: Dockerfile }
    env_file: .env
    environment: { PORT: "8000" }
    depends_on: [redis]

  celery_worker:
    build: { context: ./backend, dockerfile: Dockerfile }
    command: celery -A workers.celery_app worker --loglevel=info --concurrency=2
    env_file: .env
    depends_on: [redis]

  frontend:
    build: { context: ./frontend, dockerfile: Dockerfile }
    # Multi-stage: node build → nginx:alpine serve

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

#### Nginx Configuration (`nginx/nginx.conf`)

```nginx
server {
  listen 80;

  location /api/ {
    proxy_pass        http://backend:8000;
    proxy_set_header  Host $host;
    proxy_set_header  X-Real-IP $remote_addr;
    proxy_read_timeout 120s;   # allow for longer generation calls
  }

  location /health {
    proxy_pass http://backend:8000/health;
  }

  location / {
    proxy_pass  http://frontend:80;
    try_files   $uri $uri/ /index.html;
  }

  gzip on;
  gzip_types text/plain application/json application/javascript text/css;
  add_header X-Frame-Options DENY;
  add_header X-Content-Type-Options nosniff;
  add_header Referrer-Policy strict-origin-when-cross-origin;
}
```

#### CI/CD Pipeline (`.github/workflows/ci.yml`)

```yaml
name: NutriPlan AI CI/CD

on:
  push:         { branches: [main, develop] }
  pull_request: { branches: [main] }

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis: { image: redis:7-alpine, ports: ["6379:6379"] }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/ -v --tb=short --cov=backend --cov-report=xml
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx tsc --noEmit
      - run: cd frontend && npm run build

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t nutriplan-backend  ./backend
      - run: docker build -t nutriplan-frontend ./frontend

  deploy:
    # Manual trigger only — prevents accidental AWS charges
    if: github.event_name == 'workflow_dispatch'
    needs: build
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}    # OIDC — no long-lived keys
          aws-region:     ${{ vars.AWS_REGION }}
      - run: |
          aws ecr get-login-password | docker login --username AWS \
            --password-stdin ${{ vars.ECR_REGISTRY }}
          docker build -t $ECR/nutriplan-backend:$GITHUB_SHA  ./backend
          docker build -t $ECR/nutriplan-frontend:$GITHUB_SHA ./frontend
          docker push $ECR/nutriplan-backend:$GITHUB_SHA
          docker push $ECR/nutriplan-frontend:$GITHUB_SHA
      - run: |
          aws cloudformation deploy \
            --template-file infra/cloudformation/template.yml \
            --stack-name nutriplan-ai \
            --parameter-overrides file://infra/cloudformation/parameters.dev.json \
            --capabilities CAPABILITY_IAM
```

#### AWS Architecture

```
Route 53 (optional custom domain)
         │
         ▼
Application Load Balancer (HTTPS, ACM certificate)
  ├── /api/*  →  Backend Target Group   (FastAPI)
  └── /*      →  Frontend Target Group  (Nginx serving React build)
         │
         ▼
ECS Fargate Cluster
  ├── Backend Service      (0.5 vCPU / 1 GB RAM)
  ├── Frontend Service     (0.25 vCPU / 512 MB RAM)
  └── Celery Worker Service (0.5 vCPU / 1 GB RAM)
         │
         ▼
External Managed Services (no VPC dependency):
  Supabase  (PostgreSQL + Storage + Auth)
  Pinecone  (Vector DB)
  Redis     (AWS ElastiCache Serverless — or keep external for demo)
  OpenAI    (outbound HTTPS)
  Mistral   (outbound HTTPS)
         │
         ▼
CloudWatch Log Groups  (/nutriplan/backend · /nutriplan/frontend · /nutriplan/worker)
```

#### CloudFormation Template Scope

| Component | Details |
|---|---|
| ECR Repositories | `nutriplan-backend`, `nutriplan-frontend`, `nutriplan-worker` |
| ECS Cluster | Fargate launch type; Container Insights enabled |
| Task Definitions | Backend: 0.5 vCPU/1 GB; Frontend: 0.25 vCPU/512 MB; Worker: 0.5 vCPU/1 GB |
| ECS Services | `desiredCount=1` each; ALB health-check grace period 60s |
| IAM Execution Role | ECR pull + CloudWatch write only; no wildcard permissions |
| CloudWatch Log Groups | 7-day retention (extend for production) |
| Security Groups | ALB SG: inbound 80/443; ECS SG: inbound from ALB SG only |
| Application Load Balancer | `/api/*` → backend; `/*` → frontend; HTTP → HTTPS redirect |
| Secrets Manager | `OPENAI_API_KEY`, `MISTRAL_API_KEY`, `SUPABASE_KEY`, `PINECONE_API_KEY`, `REDIS_URL` |

> **💡 Cost control:** Run `aws cloudformation delete-stack --stack-name nutriplan-ai` after the demo. Use ECS Fargate Spot tasks (up to 70% cheaper). Set a CloudWatch billing alarm at $20. For Redis, use an external free-tier Redis provider (Upstash) during the demo to avoid ElastiCache costs.

#### Week 5 Acceptance Criteria

- [ ] `docker-compose up` starts all five services (Nginx, backend, Celery worker, frontend, Redis) without errors.
- [ ] Frontend accessible at `http://localhost`; `/health` returns HTTP 200.
- [ ] Doctor can log in, create a patient, generate a plan, and approve it through the Dockerised stack.
- [ ] CI pipeline: all pytest tests pass + TypeScript check passes + frontend build succeeds on push to main.
- [ ] CI pipeline builds all Docker images without errors.
- [ ] `aws cloudformation deploy` creates the stack without errors.
- [ ] App is accessible via the ALB DNS name.
- [ ] CloudWatch log streams show structured JSON logs for backend, frontend, and worker.
- [ ] No API keys are in CloudFormation parameters, Docker images, or GitHub Actions logs (verified by inspection).
- [ ] `docs/AWS_DEPLOYMENT.md` documents the full deploy and teardown process.
- [ ] `PROGRESS.md` marked fully complete.

---

## 12. Non-Functional Requirements

| # | Requirement | Details |
|---|---|---|
| NFR-1 | **Allergen Safety** | HARD CONSTRAINT in prompt + synonym expansion + fuzzy post-gen validator + 3-retry regeneration. All violations logged to `audit_logs`. |
| NFR-2 | **Security** | No keys in Git. `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` are backend-only secrets — never sent to the browser. FastAPI verifies JWTs locally with `python-jose` (HS256, `SUPABASE_JWT_SECRET`) — no Supabase round-trip per request. Supabase RLS enforced at the database level on all patient tables. Supabase Storage bucket is private — access only via signed URLs with expiry. AWS Secrets Manager holds all secrets in production. |
| NFR-3 | **Performance** | OCR and plan generation are async Celery tasks with polling. MacroSlider recalculation is client-side. Recipe library DB query is primary (fast); external search is fallback only. |
| NFR-4 | **Reliability** | Celery tasks are durable — survive server restart. LLM failures return HTTP 502 with retry option. OCR failures logged without crashing. 3-retry logic for allergen/repeat violations. |
| NFR-5 | **Explainability** | Every meal includes `clinical_note` explaining which conditions/rules influenced it. Allergen exclusions are listed in the plan metadata. Audit log traces every key decision. |
| NFR-6 | **Data Privacy** | Patient PII not in logs (UUIDs only). PDFs in private Supabase Storage (signed URLs). HTTPS in production. RLS prevents cross-doctor data access. |
| NFR-7 | **Maintainability** | SQLAlchemy ORM + Alembic migrations. Modular service layer. `condition_rules.json` and `medication_rules.json` editable without code changes. pytest coverage for all core services. |
| NFR-8 | **Observability** | Structlog JSON logs with request IDs and task IDs. Celery task status in Redis + DB. CloudWatch dashboards in production. |

---

## 13. Tool Recommendations & Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **ORM** | SQLAlchemy 2.0 | Type-safe, testable, DB-agnostic; essential for Alembic migrations |
| **Migrations** | Alembic | Schema evolves across 5 weeks; raw SQL files don't scale |
| **Background jobs** | Celery + Redis | Durable, survives restarts; retryable; better than FastAPI BackgroundTasks for OCR and AI generation |
| **Vector DB** | Pinecone (default) / pgvector (< 10k patients) | Single config flag: `VECTOR_BACKEND=pinecone\|pgvector` |
| **Recipe source** | Internal `recipe_library` first, then DuckDuckGo + USDA | Scraping AllRecipes is fragile; curated DB is fast and reliable |
| **Nutritional data** | USDA FoodData Central API | Free, authoritative, no key required for basic queries |
| **Allergen synonyms** | Open Food Facts taxonomy (local) | Fast (no network call per request); comprehensive |
| **Form library** | React Hook Form + Zod | Best-in-class; Zod schemas can be shared between frontend and backend |
| **PDF generation** | WeasyPrint | Python-native, free, renders HTML/CSS beautifully; no headless browser |
| **Auth** | Supabase Auth (email/password) | Built-in JWT issuance, session management, password reset — zero auth code to write or maintain |
| **JWT verification** | python-jose (HS256) | FastAPI decodes Supabase JWTs locally using `SUPABASE_JWT_SECRET` — no Supabase API call per request; sub claim used as doctor UUID |
| **Database isolation** | Supabase RLS | Row-level security enforced at the DB level with `auth.uid()` policies — safety net independent of application code |
| **File storage** | Supabase Storage | Private bucket; signed URLs with expiry for PDF access; no extra infrastructure |
| **IaC** | CloudFormation | Matches client spec; tightly integrated with AWS; no extra tooling |
| **CI auth to AWS** | OIDC (no long-lived keys) | Security best practice; eliminates rotating key management |
| **Logging** | structlog | JSON structured logs with bound context (request_id, patient_id, task_id) |

---

## 14. PROGRESS.md Instructions

```markdown
# NutriPlan AI — Project Progress

## Current Week: [1 / 2 / 3 / 4 / 5]
## Last Updated: [YYYY-MM-DD]

---

## Week 1 — Backend Foundation + Frontend Skeleton
- [ ] Docker Compose starts all services
- [ ] Supabase schema deployed via Alembic migration
- [ ] RLS policies active and tested
- [ ] Doctor auth endpoints working
- [ ] Patient CRUD endpoints passing
- [ ] PDF upload to Supabase Storage
- [ ] Rate limiting configured
- [ ] Login page and dashboard accessible in browser
- [ ] pytest tests/test_api.py passing
- [ ] README.md complete
Status: Not Started / In Progress / Complete

## Week 2 — Mistral OCR + Medical Profile Builder + Embeddings
- [ ] Celery OCR task processes sample PDF
- [ ] Blood markers extracted with is_abnormal flags
- [ ] OCR allergens saved (source='ocr_extracted')
- [ ] Medical Profile Builder normalises and merges data
- [ ] medical_profiles table upserted
- [ ] Pinecone embedding created per patient
- [ ] Patient profile page shows blood results
- [ ] Doctor can edit medical profile
- [ ] audit_logs records OCR + profile events
- [ ] Both new test files passing
Status: Not Started / In Progress / Complete

## Week 3 — Diet Plan Generation Engine
- [ ] Celery generation task produces 112-meal plan
- [ ] Allergen guard validates all meals (no violations in test plan)
- [ ] No-repeat validator (including Levenshtein) passes
- [ ] Medical condition rules reflected in plan
- [ ] Medication interactions applied
- [ ] Recipe service populates URLs for ≥ 60% of meals
- [ ] Single-meal regeneration endpoint works
- [ ] serving_multiplier PATCH scales correctly
- [ ] All six new tests passing
Status: Not Started / In Progress / Complete

## Week 4 — Full Frontend UI + Doctor Review + PDF Export
- [ ] All 7 steps of patient form save correctly
- [ ] OCR progress shows in UI; results appear in profile
- [ ] Generate Plan page with favourite food selector
- [ ] Plan Review page: edit, regenerate single meal
- [ ] MacroSlider real-time scaling works
- [ ] Approve button saves plan with correct status
- [ ] PDF export downloads correctly
- [ ] npm run build zero TypeScript errors
Status: Not Started / In Progress / Complete

## Week 5 — Docker, Nginx, CI/CD & AWS
- [ ] docker-compose up starts all 5 services
- [ ] CI pipeline tests pass
- [ ] CI builds all Docker images
- [ ] CloudFormation stack deploys
- [ ] App accessible via ALB URL
- [ ] CloudWatch logs visible
- [ ] AWS_DEPLOYMENT.md with teardown steps
Status: Not Started / In Progress / Complete

---

## Blockers
- [Description + which week it affects]

## Known Issues
- [Bug description — log detail in bugs/ folder]

## Notes
- [Decisions made, scope changes, context]
```

**Rules:** Update at the end of every working session. Never mark complete until acceptance criteria are verified. Blockers unresolved in the same session must be listed. Keep the full history — do not delete previous weeks.

---

## 15. Final Demo Flow

1. Architecture walkthrough — data flow from login to PDF.
2. Doctor login through the browser.
3. Dashboard — patient list, search.
4. Create new patient — walk through all 7 form steps.
5. Upload blood-test PDF — Celery task queued.
6. OCR completes — blood markers appear; abnormal values highlighted in red.
7. Medical Profile auto-built — conditions normalised, allergen synonyms expanded, constraints shown.
8. Navigate to Generate Plan — select 4-week plan; choose 6 favourite foods (allergic foods blocked).
9. Generation runs — progress shown via task polling.
10. Plan Review page loads — calendar grid with all 112 meals.
11. Click a meal — slide-out shows ingredients, `clinical_note`, recipe link.
12. Regenerate a single meal — confirm only that cell changes.
13. Demonstrate no-repeat — show no dish appears twice in Week 1.
14. Demonstrate medical constraint — confirm no soy for hypothyroid patient.
15. Approve Plan — `status` set to `approved`; redirect to plan view.
16. MacroSlider at 1.5× — quantities and macros update in real time.
17. Export PDF — open downloaded diet chart; allergen banner visible.
18. Audit Logs — show event trail in the UI.
19. `docker-compose up` — all 5 services healthy.
20. GitHub Actions — push a commit; CI runs; all green.
21. AWS — CloudFormation stack in console; app live via ALB URL.
22. CloudWatch — structured JSON logs in browser.
23. Teardown — `aws cloudformation delete-stack` removes all resources.

---

## 16. Production Risks & Mitigations

### AI Risks

| Risk | Mitigation |
|---|---|
| **Allergen hallucination** | HARD STOP prompt language + synonym expansion + fuzzy post-gen validation + 3-retry regeneration + `audit_logs` records every violation |
| **Nutritional inaccuracy** | USDA FoodData Central grounds all calorie/macro values; LLM provides names and quantities, not nutritional facts |
| **Outdated medication rules** | Static JSON files are version-controlled; doctor reviews plan before approval; plan only goes to `approved` on explicit doctor action |
| **OCR extraction errors** | Raw OCR text stored for audit; OCR-extracted allergens marked `source='ocr_extracted'` for doctor review before generation |
| **Dish near-duplicate slip-through** | Levenshtein distance < 8 catches "Chicken Pasta" vs "Chicken Pasta Bake"; fuzzy allergen matching catches "oat bran" vs "oats" |
| **Hallucinated medical advice** | `clinical_note` is explanatory only; system prompt explicitly states: "Do not provide diagnostic or emergency medical advice" |

### Engineering Risks

| Risk | Mitigation |
|---|---|
| **API key leakage** | `.env.example` only in Git; AWS Secrets Manager in production; GitHub secret scanning enabled |
| **Celery task loss on restart** | Redis persistence (`appendonly yes`); Celery task result backend stores state |
| **Supabase RLS misconfiguration** | Integration test: second doctor cannot read another doctor's patients |
| **Plan generation timeout** | Async Celery task; frontend polls `/status`; 90s Nginx proxy timeout; user-friendly error with retry |
| **Recipe scraping breakage** | Internal `recipe_library` is primary source; USDA is nutritional fallback; recipe URL is optional |
| **Schema drift** | Alembic migration per schema change; CI runs `alembic check` to fail if unapplied migrations exist |

### Deployment Risks

| Risk | Mitigation |
|---|---|
| **AWS cost overrun** | ECS Fargate Spot; CloudWatch billing alarm at $20; `delete-stack` teardown in docs |
| **Incorrect IAM permissions** | Minimal IAM: ECR pull + CloudWatch write only; no wildcards; OIDC replaces long-lived keys |
| **Secrets in CloudWatch logs** | structlog never logs request bodies or env vars; patient data logged as UUIDs only |
| **No rollback** | CloudFormation retains previous task definition; rollback = one `update-service` CLI command |
| **Redis data loss** | Use Redis `appendonly yes`; Celery tasks are idempotent (safe to re-run) |

---

## 17. Future Enhancements (Phase 2)

- **Patient mobile app** — view diet plan, log meals, track adherence
- **WhatsApp delivery** — send daily meal reminders via WhatsApp API
- **Grocery list generation** — auto-generate weekly shopping list from plan
- **Barcode scanning** — patient scans food; app checks against allergens and macros
- **Wearable integration** — import activity data (Apple Health, Fitbit) to adjust calorie targets
- **Multilingual plans** — generate meal plans in patient's native language
- **Patient feedback loop** — patient rates meals; system learns preferences
- **AI chatbot follow-up** — patient asks diet questions; RAG answers from their plan
- **Calendar reminders** — sync meal plan to patient's Google or Apple calendar
- **Progress tracking** — weight and BMI trend charts over time
- **Multi-doctor clinics** — team accounts with shared patient access and role-based permissions

---

## 18. Delivery Summary

| Week | Deliverable |
|---|---|
| **Week 1** | FastAPI backend + SQLAlchemy + Alembic migrations + Supabase Auth + RLS-enforced patient CRUD + Celery/Redis wired + Docker Compose + minimal frontend (login + dashboard) |
| **Week 2** | Mistral OCR Celery pipeline + Medical Profile Builder (normalise + merge + synonym expansion) + Pinecone embeddings + patient profile UI with blood results |
| **Week 3** | GPT-4o generation engine + allergen guard (fuzzy + synonym) + no-repeat validator (Levenshtein) + recipe service (library → DuckDuckGo → USDA) + single-meal regeneration + macro parametrisation |
| **Week 4** | Full React frontend: 7-step patient wizard (RHF + Zod) + OCR progress + plan review/edit/approve + MacroSlider (real-time) + WeasyPrint PDF export + audit log UI |
| **Week 5** | Nginx + Docker Compose (5 services) + GitHub Actions CI/CD (OIDC to AWS) + AWS ECS Fargate + CloudFormation IaC + CloudWatch logs + teardown guide |

---

> **Total: 5 weeks** from zero to a cloud-deployed, fully reviewed, clinical-grade nutrition AI platform — with absolute allergen safety, medically-aware dietary reasoning, durable async job processing, doctor review workflows, and real-time parametrisable macros.
