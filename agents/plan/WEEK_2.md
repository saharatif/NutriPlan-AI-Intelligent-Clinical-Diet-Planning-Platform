# Week 2 — Mistral OCR + Medical Profile Builder + Embeddings

## Goal
Upload a blood-test PDF → Celery processes it with Mistral OCR → structured blood markers stored → allergens auto-populated → Medical Profile built and normalised → patient embedding upserted into Pinecone (or pgvector).

---

## Deliverables

### Backend
| File | Purpose |
|---|---|
| `backend/services/ocr_service.py` | Call Mistral OCR API, parse response into structured blood markers / allergens / conditions |
| `backend/services/medical_profile_service.py` | Normalise conditions, expand allergen synonyms, resolve medication interactions, build `nutrition_constraints`, upsert `medical_profiles` |
| `backend/services/embedding_service.py` | Build embedding text from medical profile → OpenAI `text-embedding-3-small` → upsert Pinecone (or pgvector) |
| `backend/services/audit_service.py` | `log(doctor_id, patient_id, event_type, metadata)` → insert into `audit_logs` |
| `backend/workers/task_ocr.py` | Celery task: `process_blood_test_pdf(document_id)` — download from Storage → OCR → parse → save markers → trigger profile build |
| `backend/workers/task_medical_profile.py` | Celery task: `build_medical_profile(patient_id)` — can be triggered standalone |
| `backend/api/routes_medical_profile.py` | `POST /build`, `GET /`, `PUT /` for medical profile |
| `backend/models/medical_profile.py` | SQLAlchemy ORM: BloodTestResult, OcrResult, MedicalProfile |
| `backend/schemas/medical_profile.py` | Pydantic v2 schemas for all new models |
| `backend/db/pinecone_client.py` | Abstraction: `upsert(patient_id, vector, metadata)`, `query(vector, top_k)` — works for both Pinecone and pgvector |
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
