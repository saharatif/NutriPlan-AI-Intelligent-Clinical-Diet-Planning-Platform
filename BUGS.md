# NutriPlan AI — Bug Log

## How to Use This File

When a bug is found, add an entry using the template below. Never delete resolved bugs — mark them `Resolved` and keep the history. Reference the bug ID in commit messages (e.g. `fix: BUG-003 — allergen synonym expansion missing soy derivatives`).

### Severity Levels
| Level | Meaning |
|---|---|
| **Critical** | Data loss, security vulnerability, allergen safety failure, app crash in production |
| **Major** | Feature broken end-to-end, test suite failing, RLS not enforced |
| **Minor** | UI glitch, cosmetic issue, non-blocking error in logs |

### Bug Entry Template
```
## BUG-XXX — Short description
- **Severity:** Critical / Major / Minor
- **Week:** Which week's deliverable is affected
- **Reported:** YYYY-MM-DD
- **Status:** Open / In Progress / Resolved
- **Resolved:** YYYY-MM-DD (if resolved)

**Symptoms:** What the developer observed.
**Root Cause:** What was actually wrong (fill in when diagnosed).
**Fix:** What was changed to resolve it (fill in when resolved).
**Files Changed:** List of files modified by the fix.
```

---

## Open Bugs

## BUG-006 — OCR parser misses pipe-delimited table format from Mistral
- **Severity:** Major
- **Week:** Week 2
- **Reported:** 2026-05-16
- **Status:** Open

**Symptoms:** Mistral OCR returns structured blood test tables as pipe-delimited rows (`| ESR | 26 * | mm/hr | ● | 0-20 |`). The current regex in `ocr_service.py` only matches colon/equals patterns (`Marker: value unit`). 109 markers were extracted from Neelam's report but ESR and other table-format markers were missed. Only noise rows (dates, page numbers) were captured.
**Root Cause:** `MARKER_PATTERN` regex in `ocr_service.py` uses `[:=-]` as the separator between name and value. Mistral's markdown table output uses `|` as separator.
**Fix:** Add a second regex pattern for pipe-delimited table rows alongside the existing colon/equals pattern. Parse both formats in `_parse_blood_markers()`.
**Files Changed:** `backend/services/ocr_service.py`

---

## BUG-005 — Celery tasks not registered — KeyError on task name
- **Severity:** Critical
- **Week:** Week 2 / cross-cutting
- **Reported:** 2026-05-16
- **Status:** Resolved
- **Resolved:** 2026-05-16

**Symptoms:** Celery worker started successfully but raised `KeyError: 'workers.task_ocr.process_blood_test_pdf'` when a task was queued. OCR and diet plan generation tasks never executed.
**Root Cause:** `celery_app.py` used `autodiscover_tasks(["workers"])` which requires task modules to be importable at the package level. The modules were not being discovered correctly.
**Fix:** Replaced `autodiscover_tasks` with an explicit `include` list in `celery_app.conf.update()` listing all three task modules: `workers.task_ocr`, `workers.task_medical_profile`, `workers.task_diet_plan`.
**Files Changed:** `backend/workers/celery_app.py`

---

## BUG-004 — Supabase Storage bucket not created — upload returns 400
- **Severity:** Critical
- **Week:** Week 1 / cross-cutting
- **Reported:** 2026-05-16
- **Status:** Resolved
- **Resolved:** 2026-05-16

**Symptoms:** PDF upload returned HTTP 500. Backend log: `StorageException: {'statusCode': 400, 'error': 'Bucket not found', 'message': 'Bucket not found'}`. Documents were not saved to DB.
**Root Cause:** The `patient-documents` Supabase Storage bucket was referenced in code and `.env` but never created in the Supabase dashboard.
**Fix:** Created the `patient-documents` bucket in Supabase dashboard (Storage → New bucket → Private). No code changes required.
**Files Changed:** None (infrastructure setup)

---

## BUG-003 — Doctor login returns 500 — FK violation on audit_logs
- **Severity:** Critical
- **Week:** Week 1 / cross-cutting
- **Reported:** 2026-05-16
- **Status:** Resolved
- **Resolved:** 2026-05-16

**Symptoms:** `POST /api/auth/login` returned HTTP 500 after JWT decode succeeded. Backend log: `asyncpg.exceptions.ForeignKeyViolationError: insert or update on table "audit_logs" violates foreign key constraint "audit_logs_doctor_id_fkey"`.
**Root Cause:** On first login, the new `Doctor` row and `AuditLog` row were both added to the SQLAlchemy session before `commit()`. PostgreSQL enforced the FK constraint immediately on the audit log INSERT before the doctor row was written.
**Fix:** Added `await db.flush()` between `db.add(doctor)` and `db.add(AuditLog(...))` so the doctor row is written to the DB before the audit log references it.
**Files Changed:** `backend/api/routes_auth.py`

---

## BUG-002 — JWT decode fails with 401 — Supabase now issues ES256 tokens
- **Severity:** Critical
- **Week:** Week 1 / cross-cutting
- **Reported:** 2026-05-16
- **Status:** Resolved
- **Resolved:** 2026-05-16

**Symptoms:** Every authenticated request returned HTTP 401. Backend log: `JWT decode failed: The specified alg value is not allowed | token_prefix=eyJhbGciOiJFUzI1NiIs`. Supabase auth was succeeding in the browser but the backend rejected the token.
**Root Cause:** Newer Supabase projects sign JWTs with ES256 (asymmetric key pair) rather than HS256 (shared secret). `deps.py` was only configured to verify HS256 using `SUPABASE_JWT_SECRET`, which is invalid for ES256 tokens.
**Fix:** `_decode_jwt()` now reads the `alg` header from the token. ES256 tokens are verified against Supabase's public JWKS endpoint (`/auth/v1/.well-known/jwks.json`); HS256 tokens continue to use the shared secret. JWKS is cached in memory with `@lru_cache`.
**Files Changed:** `backend/api/deps.py`

---

## BUG-001 — PatientStepForm accepts only one item per clinical category
- **Severity:** Major
- **Week:** Week 4
- **Reported:** 2026-05-16
- **Status:** Resolved
- **Resolved:** 2026-05-16

**Symptoms:** The 7-step patient wizard stores a single string per step — one condition, one medication, one allergen, one favourite food. A doctor cannot record multiple conditions or allergens for the same patient through the UI.
**Root Cause:** Each step uses a single controlled `<input>` with `useState`. The payload builder wraps the value in a one-element array (`condition ? [{ name: condition }] : []`). No add/remove list UI was built.
**Fix:** Replace each step's single input with a dynamic list — an input + Add button that pushes items into a local array, with an ✕ chip to remove each item. The `PatientPayload` type already accepts arrays; only the form needs updating.
**Files Changed:** `frontend/src/components/PatientStepForm.tsx`

---

## Resolved Bugs

_All resolved bugs are listed inline above with **Status: Resolved** and a resolution date._
