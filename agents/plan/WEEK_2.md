# Week 2 — Mistral OCR + Medical Profile Builder + Embeddings

## Goal
Upload a blood-test PDF → Celery processes it with Mistral OCR → structured blood markers stored → allergens auto-populated → Medical Profile built and normalised → patient embedding upserted into Pinecone (or pgvector).

---

## Deliverables

### Backend
| File | Purpose |
|---|---|
| `backend/services/ocr_service.py` | Mistral OCR via base64 `document_url` JSON body (not multipart); parses blood markers, allergens, conditions |
| `backend/services/medical_profile_service.py` | Normalise conditions, expand allergen synonyms, resolve medication interactions, build `nutrition_constraints`, upsert `medical_profiles` |
| `backend/services/embedding_service.py` | Medical profile embedding (single vector) + document chunker + batch embed → upsert to Pinecone or pgvector |
| `backend/services/audit_service.py` | `log(doctor_id, patient_id, event_type: AuditEvent, metadata)` → insert into `audit_logs` |
| `backend/workers/task_ocr.py` | Celery task: OCR → parse → save markers → chunk + embed document → build medical profile |
| `backend/workers/task_medical_profile.py` | Celery task: `build_medical_profile(patient_id)` — can be triggered standalone |
| `backend/api/routes_medical_profile.py` | `POST /build`, `GET /`, `PUT /` for medical profile |
| `backend/models/medical_profile.py` | SQLAlchemy ORM: BloodTestResult, OcrResult, MedicalProfile, PatientVector |
| `backend/schemas/medical_profile.py` | Pydantic v2 schemas for all new models |
| `backend/db/pinecone_client.py` | Dual-backend abstraction: pgvector (default, JSON storage) or Pinecone SDK; `upsert`, `query`, `upsert_document_chunks`, `query_document_chunks` |
| `backend/utils/clinical_rules.py` | Shared `CONDITION_ALIASES` + `KNOWN_ALLERGENS` — single source of truth for both OCR and Medical Profile services |
| `data/allergen_synonyms.json` | Open Food Facts taxonomy — loaded at startup, never fetched at runtime |
| `tests/test_ocr_service.py` | Unit tests with a fixture PDF |
| `tests/test_medical_profile_service.py` | Unit tests: normalisation, synonym expansion, constraint builder |

### Frontend
| File | Purpose |
|---|---|
| `frontend/src/pages/PatientProfile.tsx` | Blood test results table (abnormal rows in red) + allergen badges + OCR status indicator |
| `frontend/src/components/OCRResultViewer.tsx` | Table: marker name, value, unit, reference range, abnormal flag |
| `frontend/src/components/MedicalProfileCard.tsx` | Shows conditions, allergens (expanded), medications, nutrition constraints |
| `frontend/src/components/AllergenBadge.tsx` | Colour-coded chip: intolerance=yellow, allergy=orange, anaphylactic=red |

---

## Mistral OCR API Format

Mistral OCR requires the document as a **base64-encoded data URL** in a JSON body — not multipart. Sending multipart returns 422.

```python
import base64
b64 = base64.standard_b64encode(pdf_bytes).decode()
response = await client.post(
    "https://api.mistral.ai/v1/ocr",
    headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "mistral-ocr-latest",
        "document": {"type": "document_url", "document_url": f"data:application/pdf;base64,{b64}"},
    },
)
```

---

## Chunker — Why It Is Needed

Blood-test PDFs are multi-page documents (8–40 KB of extracted text). Embedding the entire document as a single vector dilutes the clinical signal — a query for "Ferritin" returns the whole document instead of the specific row. The chunker splits OCR text into focused 400-character windows with 80-character overlap, snapping boundaries to the nearest newline so no marker row is split across chunks.

```
Chunking parameters (embedding_service.py):
  CHUNK_SIZE    = 400 chars   (~100 tokens — well within text-embedding-3-small limit)
  CHUNK_OVERLAP = 80  chars   (keeps context across chunk boundaries)
  Boundary snap: rfind('\n') in second half of chunk
```

Each chunk is embedded independently and stored in Pinecone with:
- `namespace`: `patient-{patient_id}`
- `id`:        `{document_id}-chunk-{index}`
- `metadata`:  patient_id, document_id, chunk_index, chunk_text (first 500 chars)

Tested on `Sahar_test_reports.pdf` (15 pages, 38,367 chars) → 137 chunks.
Query "What is Sahar's Ferritin?" → top result score 0.60, returned exact row: **Ferritin 11.30 ng/mL (LOW, ref 13–150)**.

---

## Celery Task: `process_blood_test_pdf`

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_blood_test_pdf(self, document_id: str):
    # 1. Download PDF bytes from Supabase Storage
    # 2. Call Mistral OCR (mistral-ocr-latest)
    # 3. Parse: blood markers → blood_test_results (is_abnormal where out of range)
    # 4. Parse: allergen mentions → patient_allergens (source='ocr_extracted')
    # 5. Parse: condition mentions → patient_conditions
    # 6. Save raw OCR text → ocr_results
    # 7. Mark document.ocr_processed = True
    # 8. Queue: build_medical_profile(patient_id)
    # 9. Write audit_log: ocr_completed
```

## Medical Profile Builder Logic

```python
async def build_medical_profile(patient_id):
    conditions  = normalise_conditions(await load_conditions(patient_id))
    allergens   = expand_allergen_synonyms(await load_allergens(patient_id))
    medications = await load_medications(patient_id)
    markers     = await load_abnormal_markers(patient_id)
    med_rules   = resolve_medication_rules(medications)
    constraints = build_constraints(conditions, allergens, med_rules)
    # → { avoid: [...], limit: [...], prefer: [...] }

    await upsert_medical_profile(patient_id, {...})
    await embedding_service.update_patient_embedding(patient_id)
    await audit_service.log(patient_id, "medical_profile_built", {...})
```

## Pinecone / pgvector Abstraction

Single config flag: `VECTOR_BACKEND=pgvector` (default) or `VECTOR_BACKEND=pinecone`

`pinecone_client.py` exposes:
- `upsert(patient_id, vector, metadata)` — works for both backends
- `query(vector, top_k, filter)` — returns list of matching patient metadata

---

## New Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/patients/{id}/documents/{doc_id}/process` | Queue Celery OCR task; returns `{task_id}` |
| GET | `/api/patients/{id}/documents/{doc_id}/status` | Poll task status: pending / processing / completed / failed |
| GET | `/api/patients/{id}/blood-tests` | Structured markers with `is_abnormal` flag |
| POST | `/api/patients/{id}/medical-profile/build` | Manually trigger profile rebuild |
| GET | `/api/patients/{id}/medical-profile` | Normalised medical profile |
| PUT | `/api/patients/{id}/medical-profile` | Doctor edits profile manually |

---

## Acceptance Criteria

- [ ] Celery OCR task processes `data/sample_blood_report.pdf` using Mistral OCR
- [ ] Blood markers extracted and saved with correct values, units, and `is_abnormal` flags
- [ ] Allergens detected in PDF saved with `source = 'ocr_extracted'`
- [ ] `ocr_results` stores full raw text (for audit)
- [ ] Medical Profile normalises conditions (e.g. "high bp" → "hypertension")
- [ ] Allergen synonyms expanded (e.g. "milk" → dairy, whey, casein, lactose, etc.)
- [ ] `nutrition_constraints` built: `{avoid, limit, prefer}`
- [ ] `medical_profiles` table upserted after each build
- [ ] Patient embedding created/updated in vector store after profile build
- [ ] Doctor views blood markers in UI — abnormal values highlighted red
- [ ] Doctor manually edits medical profile via UI — changes persist
- [ ] `audit_logs` records `ocr_completed` and `medical_profile_built`
- [ ] `pytest tests/test_ocr_service.py` passes
- [ ] `pytest tests/test_medical_profile_service.py` passes
- [ ] `PROGRESS.md` updated

---

## Environment Variables Added This Week

```bash
MISTRAL_API_KEY=
OPENAI_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=nutriplan-patients
VECTOR_BACKEND=pgvector
```
