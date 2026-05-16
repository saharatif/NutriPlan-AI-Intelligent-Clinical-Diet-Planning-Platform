import re
from difflib import SequenceMatcher


def _normalise_name(value: str) -> str:
    value = re.sub(r"\bweek\s+\d+\b", "", value.lower())
    value = re.sub(r"\bday\s+\d+\b", "", value)
    value = re.sub(r"\b(mon|tue|wed|thu|fri|sat|sun)\w*\b", "", value)
    return re.sub(r"[^a-z0-9 ]+", " ", value).strip()


class NoRepeatService:
    def validate_no_repeats(self, meal: dict, assigned_meals_this_week: list[dict], threshold: float = 0.9) -> list[dict]:
        current = _normalise_name(meal.get("meal_name", ""))
        violations: list[dict] = []
        for existing in assigned_meals_this_week:
            existing_name = _normalise_name(existing.get("meal_name", ""))
            if current == existing_name or SequenceMatcher(None, current, existing_name).ratio() >= threshold:
                violations.append({"meal_name": meal.get("meal_name"), "conflicts_with": existing.get("meal_name")})
        return violations

    def validate_plan_no_repeats(self, meals: list[dict], threshold: float = 0.9) -> list[dict]:
        violations: list[dict] = []
        by_week: dict[int, list[dict]] = {}
        for meal in meals:
            week = int(meal["week"])
            assigned = by_week.setdefault(week, [])
            violations.extend(self.validate_no_repeats(meal, assigned, threshold))
            assigned.append(meal)
        return violations
