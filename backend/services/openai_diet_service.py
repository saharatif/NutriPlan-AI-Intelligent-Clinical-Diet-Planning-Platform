import json
from pathlib import Path

import httpx

from utils.config import settings


class OpenAIDietService:
    def is_enabled(self) -> bool:
        return bool(settings.OPENAI_API_KEY) and settings.DIET_PLAN_GENERATION_PROVIDER == "openai"

    async def generate_meal(
        self,
        *,
        week: int,
        day: int,
        meal_slot: str,
        conditions: list[str],
        allergens: list[str],
        restrictions: list[str],
        selected_favourites: list[str],
        assigned_meals_this_week: list[str],
        ethnicity: str | None = None,
        dietary_preference: str | None = None,
    ) -> dict:
        prompt = {
            "task": "Generate exactly one clinically appropriate meal. Return JSON only.",
            "schema": {
                "meal_name": "string",
                "clinical_note": "string",
                "ingredients": [{"name": "string", "quantity": "number", "unit": "string"}],
                "base_calories": "integer",
                "base_protein_g": "number",
                "base_fat_g": "number",
                "base_carbs_g": "number",
                "recipe_url": "string or null",
                "recipe_steps": ["Step 1 as a clear sentence.", "Step 2...", "...5-8 steps total"]
            },
            "patient_profile": {
                "medical_conditions": conditions,
                "allergens_never_include": allergens,
                "food_restrictions_from_conditions_and_medications": restrictions,
                "patient_favourite_foods": selected_favourites,
                **({"ethnicity": ethnicity} if ethnicity else {}),
                **({"dietary_preference": dietary_preference} if dietary_preference else {}),
            },
            "meal_slot_context": {
                "week": week,
                "day": day,
                "meal_slot": meal_slot,
                "meals_already_assigned_this_week": assigned_meals_this_week,
            },
            "hard_rules": [
                "NEVER include any allergen or its synonyms, derivatives, or hidden forms — this is a patient safety requirement.",
                "Apply all food_restrictions_from_conditions_and_medications strictly.",
                "Do not repeat or closely resemble any meal already assigned this week.",
                "Use base serving 1.0 nutritional values.",
                *(
                    [f"FAVOURITE FOODS: The patient enjoys {', '.join(selected_favourites)}. Actively incorporate one of these as the main ingredient or key component in this meal if clinically appropriate and not allergen-conflicting."]
                    if selected_favourites else []
                ),
                *(
                    [f"CULTURAL CONTEXT: Patient is {ethnicity}. Where appropriate, use culturally relevant ingredients, spices, and cooking methods."]
                    if ethnicity else []
                ),
                *(self._dietary_preference_rules(dietary_preference) if dietary_preference else []),
            ],
        }

        async with httpx.AsyncClient(timeout=settings.OPENAI_DIET_TIMEOUT_SECONDS) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.OPENAI_DIET_MODEL,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": self._system_prompt()},
                        {"role": "user", "content": json.dumps(prompt)},
                    ],
                    "temperature": 0.35,
                },
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._normalise_meal(json.loads(content))

    async def generate_recipe_steps(self, meal_name: str, ingredients: list[dict]) -> list[str]:
        ingredient_list = ", ".join(
            f"{i.get('quantity')} {i.get('unit')} {i.get('name')}" for i in ingredients
        )
        prompt = (
            f"Write clear, numbered cooking steps for '{meal_name}' using these ingredients: {ingredient_list}. "
            "Return a JSON object with a single key 'steps' containing an array of strings. "
            "Each step should be one concise sentence. Aim for 5-8 steps."
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.OPENAI_DIET_MODEL,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "You are a clinical nutritionist. Return only valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
        data = response.json()["choices"][0]["message"]["content"]
        return json.loads(data).get("steps", [])

    def _normalise_meal(self, meal: dict) -> dict:
        raw_steps = meal.get("recipe_steps")
        steps = raw_steps if isinstance(raw_steps, list) and all(isinstance(s, str) for s in raw_steps) else []
        return {
            "meal_name": str(meal.get("meal_name") or "Clinical Balanced Plate"),
            "clinical_note": str(meal.get("clinical_note") or "balanced clinical meal"),
            "ingredients": meal.get("ingredients") if isinstance(meal.get("ingredients"), list) else [],
            "base_calories": int(meal.get("base_calories") or 400),
            "base_protein_g": float(meal.get("base_protein_g") or 24),
            "base_fat_g": float(meal.get("base_fat_g") or 14),
            "base_carbs_g": float(meal.get("base_carbs_g") or 42),
            "recipe_url": meal.get("recipe_url"),
            "recipe_steps": steps or None,
        }

    def _dietary_preference_rules(self, preference: str) -> list[str]:
        rules: dict[str, list[str]] = {
            "vegan": [
                "Patient is VEGAN. Strictly exclude all animal products: no meat, poultry, fish, seafood, dairy, eggs, or honey.",
                "Use only plant-based proteins: legumes, tofu, tempeh, seitan, nuts, seeds.",
            ],
            "vegetarian": [
                "Patient is VEGETARIAN. Exclude all meat, poultry, fish, and seafood.",
                "Dairy and eggs are permitted. Use plant-based proteins and eggs/dairy as needed.",
            ],
            "pescatarian": [
                "Patient is PESCATARIAN. Exclude all meat and poultry (no chicken, beef, pork, lamb, turkey).",
                "Fish and seafood are permitted. Dairy and eggs are also permitted.",
            ],
            "flexitarian": [
                "Patient is FLEXITARIAN (mostly plant-based). Prioritise plant-based meals.",
                "Small amounts of meat or fish are acceptable occasionally — no more than 1–2 meals per week should contain meat.",
            ],
        }
        return rules.get(preference.lower(), [])

    def _system_prompt(self) -> str:
        path = Path(__file__).resolve().parents[1] / "prompts" / "diet_plan_system.txt"
        return path.read_text(encoding="utf-8")
