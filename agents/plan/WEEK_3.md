# Week 3 — Diet Plan Generation Engine

## Goal
`POST /diet-plans/generate` queues a Celery task → GPT-4o generates a 112-meal 4-week plan → no allergens in any meal → no dish repeats within a week → condition and medication rules applied → serving-multiplier scaling works → single-meal regeneration works.

---

## Deliverables

### Backend
| File | Purpose |
|---|---|
| `backend/services/diet_plan_service.py` | Orchestrates the full generation workflow: load profile → RAG → build prompt → call GPT-4o → validate → persist |
| `backend/services/recipe_service.py` | Recipe lookup: `recipe_library` DB → DuckDuckGo → USDA FoodData Central |
| `backend/services/allergen_service.py` | `expand_allergens()` + `validate_plan_allergens()` (fuzzy match via rapidfuzz) |
| `backend/services/no_repeat_service.py` | `validate_no_repeats()` using Levenshtein distance (rapidfuzz) |
| `backend/services/macro_service.py` | `scale_meal(meal, multiplier)` — pure function, no DB call |
| `backend/workers/task_diet_plan.py` | Celery task: `generate_diet_plan(patient_id, selected_favourites, plan_type)` |
| `backend/api/routes_diet_plans.py` | Generate, status poll, list plans, full plan detail, approve |
| `backend/api/routes_meals.py` | PATCH multiplier, POST regenerate single/day/full |
| `backend/models/diet_plan.py` | SQLAlchemy: DietPlan, DietPlanMeal, RecipeLibrary |
| `backend/schemas/diet_plan.py` | Pydantic v2 schemas |
| `backend/prompts/diet_plan_system.txt` | GPT-4o system prompt template (see plan Section 7.1) |
| `backend/prompts/condition_rules.json` | Medical condition → dietary rules |
| `backend/prompts/medication_rules.json` | Medication → food interaction rules |
| `data/allergen_synonyms.json` | (Already created in Week 2) |
| `tests/test_allergen_service.py` | Fuzzy match, synonym expansion, allergen violation detection |
| `tests/test_no_repeat_service.py` | Exact match + Levenshtein near-duplicate detection |
| `tests/test_macro_service.py` | `scale_meal()` at 0.5×, 1.0×, 1.5×, 3.0× with floating-point precision checks |
| `tests/test_diet_plan_service.py` | Integration test: generate plan for test patient, assert 112 meals, no allergens, no repeats |

---

## Generation Workflow (inside Celery task)

```
For each week (1–4):
  assigned_meals_this_week = []
  For each day (Mon–Sun):
    For each meal_slot (Breakfast, Lunch, Snack, Dinner):
      attempt = 0
      while attempt < 3:
        meal = call_gpt4o(prompt_with_context)
        if allergen_guard.validate(meal, allergens) has violations:
            log audit: allergen_violation_detected
            attempt += 1; continue
        if no_repeat_service.validate(meal, assigned_meals_this_week) has violations:
            log audit: no_repeat_violation_detected
            attempt += 1; continue
        meal = recipe_service.enrich(meal)  # ground macros via USDA
        assigned_meals_this_week.append(meal)
        break
      else:
        use fallback safe meal and log warning

Persist all 112 meals → diet_plan_meals
Update diet_plans.status = 'draft'
Write audit_log: diet_plan_generation_completed
```

---

## Serving Multiplier Design

Values stored at **base serving (1.0×)**. All scaling is **client-side, no API call**.

```typescript
// macroUtils.ts
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
```

`PATCH /api/diet-plans/{plan_id}/meals/{meal_id}` — persists the doctor's chosen multiplier, does not recalculate server-side.

---

## New Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/patients/{id}/diet-plans/generate` | Queue Celery task; return `{task_id}` |
| GET | `/api/patients/{id}/diet-plans/generate/{task_id}/status` | Poll: pending / running / completed / failed |
| GET | `/api/patients/{id}/diet-plans` | List saved plans |
| GET | `/api/diet-plans/{plan_id}` | Full plan: all 112 meals with ingredients |
| PATCH | `/api/diet-plans/{plan_id}/meals/{meal_id}` | Update `serving_multiplier` |
| POST | `/api/diet-plans/{plan_id}/meals/{meal_id}/regenerate` | Regenerate single meal |
| POST | `/api/diet-plans/{plan_id}/days/{week}/{day}/regenerate` | Regenerate full day |
| POST | `/api/diet-plans/{plan_id}/regenerate` | Regenerate full plan |

---

## Acceptance Criteria

- [ ] Celery task generates a 4-week plan (112 meals) for a test patient
- [ ] All meals have: `meal_name`, `base_calories`, macros, and populated `ingredients` array
- [ ] Zero allergen violations in any meal (including synonyms) — verified by test
- [ ] Zero dish repeats within any single week (including near-duplicates) — verified by test
- [ ] Same dish may reappear in a different week with modified name
- [ ] Medical condition rules reflected (no soy for hypothyroid; low sodium for hypertensive)
- [ ] Medication interactions applied (no grapefruit for statin patient)
- [ ] Recipe source URLs populated for ≥ 60% of meals
- [ ] `PATCH serving_multiplier = 1.5` returns correctly scaled values
- [ ] Single-meal regeneration replaces only the targeted meal
- [ ] `audit_logs` records `diet_plan_generation_completed` and any violation events
- [ ] All four test files pass: allergen, no-repeat, macro, diet_plan
- [ ] `PROGRESS.md` updated

---

## Environment Variables (same as Week 2 — no new vars)
