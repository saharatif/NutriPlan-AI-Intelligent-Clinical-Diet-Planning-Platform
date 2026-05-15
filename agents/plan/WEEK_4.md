# Week 4 — Full Frontend UI + Doctor Review + PDF Export

## Goal
A doctor can do the entire clinical workflow from the browser: create a patient → upload a blood report → see OCR results → generate a plan → review and edit meals → adjust macros with sliders → approve the plan → download a formatted PDF diet chart.

---

## Deliverables

### Frontend Pages
| Route | Component | Description |
|---|---|---|
| `/login` | `Login.tsx` | Email + password; Supabase Auth; redirect on success; error handling |
| `/` | `Dashboard.tsx` | Patient list with search + filter; quick stats cards; Add Patient CTA |
| `/patients/new` | `NewPatient.tsx` | 7-step wizard: all steps complete (see below) |
| `/patients/:id` | `PatientProfile.tsx` | Blood test results; allergen badges; OCR status; medical profile; saved plans list |
| `/patients/:id/generate` | `GenerateDietPlan.tsx` | Plan type selector; favourite food selector; async progress bar with task polling |
| `/diet-plans/:id/review` | `DietPlanReview.tsx` | Draft plan calendar; click meal → edit/regenerate; approve button |
| `/diet-plans/:id` | `DietPlan.tsx` | Approved plan; week tabs; MacroSlider on every meal; recipe links; Export PDF |

### Frontend Components
| Component | Description |
|---|---|
| `Layout.tsx` | Sidebar nav + header + main content area |
| `PatientCard.tsx` | Card in dashboard list: patient_code, name, BMI, last plan date |
| `MealCard.tsx` | Meal in calendar grid: name, kcal, P/F/C chips |
| `MacroSlider.tsx` | 0.5× to 3.0× in 0.25 steps; updates quantities and macros in real time via `scaleMeal()` |
| `AllergenBadge.tsx` | Colour-coded chip: intolerance=yellow, allergy=orange, anaphylactic=red |
| `WeekCalendar.tsx` | 7-day × 4-meal grid; colour-coded by meal type; click → MealDetailPanel |
| `MealDetailPanel.tsx` | Slide-out: ingredients list, macros, clinical_note, recipe link, MacroSlider |
| `MealEditModal.tsx` | Free-text meal edit form + Regenerate button; posts to `/meals/{id}/regenerate` |
| `PatientStepForm.tsx` | 7-step wizard using React Hook Form + Zod (see step list below) |
| `OCRResultViewer.tsx` | Table: marker name, value, unit, reference range; abnormal rows highlighted red |
| `MedicalProfileCard.tsx` | Conditions, expanded allergens, medications, nutrition constraints |
| `AuditLogTable.tsx` | Paginated event log: event_type, timestamp, metadata |

### Backend — New This Week
| File | Purpose |
|---|---|
| `backend/services/pdf_export_service.py` | WeasyPrint: render `diet_chart.html` → PDF → upload to Supabase Storage → return signed URL |
| `backend/api/routes_export.py` | `POST /export/pdf`, `GET /download` |
| `backend/api/routes_audit.py` | `GET /api/patients/{id}/audit-logs`, `GET /api/audit-logs` |
| `backend/exports/templates/diet_chart.html` | WeasyPrint HTML template (see PDF layout below) |
| `tests/test_audit_service.py` | Verify all key events are logged with correct fields |

---

## 7-Step Patient Wizard

```
Step 1: Basic Info         name, DOB, gender, ethnicity, height_cm, weight_kg, BMI (auto-calculated)
Step 2: Conditions         condition_name, severity (mild/moderate/severe), notes
Step 3: Medications        medication_name, dosage_mg, frequency
Step 4: Allergens          allergen, severity (intolerance/allergy/anaphylactic)
Step 5: Family History     condition, relation (father/mother/sibling/other)
Step 6: Favourite Foods    20–25 items: food_name, cuisine_type, meal_type preference
Step 7: Documents + Review PDF upload (triggers OCR on save), full summary, Save button
```

On successful save:
- Toast: "Patient saved! Would you like to generate a diet plan?"
- Buttons: "1-Week Plan" / "4-Week Plan" → navigate to GenerateDietPlan

---

## Doctor Review Page

```
WeekCalendar grid (read-only, colour-coded by meal type)
│
├── Click any meal cell → MealDetailPanel (right slide-out):
│     ├── Full ingredient list with quantities
│     ├── Calories + macros (base values)
│     ├── clinical_note (why this meal / constraints applied)
│     ├── Recipe link (opens in new tab)
│     ├── "Edit Meal" → MealEditModal (free-text + regenerate)
│     └── "Regenerate This Meal" → POST .../regenerate
│
├── "Regenerate Day" button (per day column header)
├── "Regenerate Full Plan" button (top right)
│
└── "Approve Plan" button (sticky footer)
      → POST /diet-plans/{id}/approve
      → Redirect to DietPlan view
```

---

## PDF Export Layout

```
Page 1: Cover
  - Patient name, patient_code, DOB, doctor name, clinic
  - Red allergen warning banner: "ALLERGEN EXCLUSIONS: [list]"
  - BMI category, active conditions, total weekly calories

Pages 2–5: One page per week
  ┌─────────────────────────────────────────────────────────┐
  │ Week N  │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │ Sun │
  ├─────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  │ Breakf. │ ... │ ... │ ... │ ... │ ... │ ... │ ... │
  │ Lunch   │ ... │ ... │ ... │ ... │ ... │ ... │ ... │
  │ Snack   │ ... │ ... │ ... │ ... │ ... │ ... │ ... │
  │ Dinner  │ ... │ ... │ ... │ ... │ ... │ ... │ ... │
  └─────────────────────────────────────────────────────────┘
  Each cell: meal_name + kcal + P/F/C (at chosen multiplier)

Page 6: Clinical Notes
  - Condition rules applied
  - Medication interactions noted
  - Doctor notes field
```

---

## New Endpoints This Week

| Method | Path | Description |
|---|---|---|
| POST | `/api/diet-plans/{plan_id}/approve` | Set status=approved, approved_at=now(), audit log |
| POST | `/api/diet-plans/{plan_id}/export/pdf` | WeasyPrint → PDF → Supabase Storage; return signed URL |
| GET | `/api/diet-plans/{plan_id}/download` | Redirect to signed URL |
| GET | `/api/patients/{id}/audit-logs` | Paginated audit log for a patient |
| GET | `/api/audit-logs` | All audit logs for the authenticated doctor |

---

## Acceptance Criteria

- [ ] `npm run dev` starts frontend on `http://localhost:5173` with no console errors
- [ ] Doctor logs in; JWT stored; all API calls carry Bearer token
- [ ] All 7 steps of New Patient form save correctly; patient appears in dashboard
- [ ] PDF upload queues OCR task; status polling shows "Processing" → "Complete"
- [ ] Blood markers appear with abnormal values highlighted red
- [ ] Medical profile visible; doctor can edit and save changes
- [ ] Generate Plan page shows favourite food selector with allergic foods disabled
- [ ] Task polling works; calendar grid renders on completion
- [ ] Click meal → slide-out shows ingredients, clinical_note, recipe link
- [ ] "Regenerate This Meal" replaces only that cell — no other meals change
- [ ] MacroSlider at 1.5× updates quantities and macros in real time (no API call)
- [ ] "Approve Plan" saves `status = 'approved'` and redirects to plan view
- [ ] Export PDF downloads correctly formatted diet chart with red allergen banner
- [ ] Audit log table shows all key events for the session
- [ ] `npm run build` succeeds with zero TypeScript errors
- [ ] `pytest tests/test_audit_service.py` passes
- [ ] `PROGRESS.md` updated
