from services.no_repeat_service import NoRepeatService


def test_exact_repeat_detected_within_week() -> None:
    service = NoRepeatService()
    meal = {"week": 1, "meal_name": "Week 1 Breakfast Quinoa Bowl"}
    assigned = [{"week": 1, "meal_name": "Week 1 Breakfast Quinoa Bowl"}]
    assert service.validate_no_repeats(meal, assigned)


def test_near_duplicate_detected() -> None:
    service = NoRepeatService()
    meal = {"week": 1, "meal_name": "Week 1 Lunch Quinoa Lentil Bowl"}
    assigned = [{"week": 1, "meal_name": "Lunch Quinoa Lentil Bowls"}]
    assert service.validate_no_repeats(meal, assigned)


def test_same_dish_in_different_week_is_allowed_by_plan_validator() -> None:
    service = NoRepeatService()
    meals = [
        {"week": 1, "meal_name": "Week 1 Breakfast Quinoa Lentil Bowl"},
        {"week": 2, "meal_name": "Week 2 Breakfast Quinoa Lentil Bowl"},
    ]
    assert service.validate_plan_no_repeats(meals) == []
