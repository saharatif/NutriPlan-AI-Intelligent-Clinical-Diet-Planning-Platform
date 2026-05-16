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
                "recipe_url": "string or null"
            },
            "context": {
                "week": week,
                "day": day,
                "meal_slot": meal_slot,
                "conditions": conditions,
                "allergens_and_synonyms_to_avoid": allergens,
                "medical_restrictions": restrictions,
                "selected_favourites": selected_favourites,
                "already_assigned_this_week": assigned_meals_this_week,
            },
            "rules": [
                "Never include allergens or allergen synonyms.",
                "Avoid soy if soy is restricted.",
                "Avoid grapefruit if grapefruit is restricted.",
                "Do not repeat or near-repeat meals already assigned this week.",
                "Use base serving 1.0 values.",
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

    def _normalise_meal(self, meal: dict) -> dict:
        return {
            "meal_name": str(meal.get("meal_name") or "Clinical Balanced Plate"),
            "clinical_note": str(meal.get("clinical_note") or "balanced clinical meal"),
            "ingredients": meal.get("ingredients") if isinstance(meal.get("ingredients"), list) else [],
            "base_calories": int(meal.get("base_calories") or 400),
            "base_protein_g": float(meal.get("base_protein_g") or 24),
            "base_fat_g": float(meal.get("base_fat_g") or 14),
            "base_carbs_g": float(meal.get("base_carbs_g") or 42),
            "recipe_url": meal.get("recipe_url"),
        }

    def _system_prompt(self) -> str:
        path = Path(__file__).resolve().parents[1] / "prompts" / "diet_plan_system.txt"
        return path.read_text(encoding="utf-8")
