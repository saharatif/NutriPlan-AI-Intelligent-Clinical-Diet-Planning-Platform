import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


class AllergenService:
    def __init__(self, allergen_path: Path | None = None):
        self.allergen_path = allergen_path or Path(__file__).resolve().parents[2] / "data" / "allergen_synonyms.json"

    def expand_allergens(self, allergens: list[str]) -> list[str]:
        synonyms = self._load_synonyms()
        expanded: list[str] = []
        for allergen in allergens:
            key = _normalise(allergen)
            expanded.append(key)
            expanded.extend(_normalise(value) for value in synonyms.get(key, []))
        return self._unique(expanded)

    def validate_meal_allergens(self, meal: dict, allergens: list[str], threshold: float = 0.88) -> list[dict]:
        expanded = self.expand_allergens(allergens)
        ingredient_texts = [_normalise(item.get("name", "")) for item in meal.get("ingredients", [])]
        ingredient_texts.append(_normalise(meal.get("meal_name", "")))
        violations: list[dict] = []
        for allergen in expanded:
            for text in ingredient_texts:
                words = text.split()
                candidates = [text, *words]
                if any(allergen == candidate or allergen in text or SequenceMatcher(None, allergen, candidate).ratio() >= threshold for candidate in candidates):
                    violations.append({"allergen": allergen, "meal_name": meal.get("meal_name"), "matched_text": text})
                    break
        return violations

    def validate_plan_allergens(self, meals: list[dict], allergens: list[str]) -> list[dict]:
        violations: list[dict] = []
        for meal in meals:
            violations.extend(self.validate_meal_allergens(meal, allergens))
        return violations

    def _load_synonyms(self) -> dict[str, list[str]]:
        with self.allergen_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
