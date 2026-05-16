from services.allergen_service import AllergenService


def test_expand_allergens_includes_synonyms() -> None:
    expanded = AllergenService().expand_allergens(["milk"])
    assert "dairy" in expanded
    assert "casein" in expanded
    assert "lactose" in expanded


def test_validate_plan_allergens_detects_synonym_violation() -> None:
    meals = [
        {
            "meal_name": "Breakfast Oats",
            "ingredients": [{"name": "whey protein", "quantity": 1, "unit": "scoop"}],
        }
    ]
    violations = AllergenService().validate_plan_allergens(meals, ["milk"])
    assert violations
    assert violations[0]["allergen"] == "whey"


def test_validate_plan_allergens_allows_safe_meal() -> None:
    meals = [{"meal_name": "Quinoa Bowl", "ingredients": [{"name": "quinoa", "quantity": 1, "unit": "cup"}]}]
    assert AllergenService().validate_plan_allergens(meals, ["peanut"]) == []
