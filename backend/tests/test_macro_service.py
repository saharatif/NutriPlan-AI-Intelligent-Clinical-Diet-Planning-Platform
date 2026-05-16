from services.macro_service import scale_meal


BASE_MEAL = {
    "meal_name": "Quinoa Bowl",
    "base_calories": 400,
    "base_protein_g": 20.0,
    "base_fat_g": 10.0,
    "base_carbs_g": 50.0,
    "ingredients": [{"name": "quinoa", "quantity": 100.0, "unit": "g"}],
}


def test_scale_meal_half() -> None:
    scaled = scale_meal(BASE_MEAL, 0.5)
    assert scaled["effective_calories"] == 200
    assert scaled["effective_protein_g"] == 10.0
    assert scaled["ingredients"][0]["quantity"] == 50.0


def test_scale_meal_one() -> None:
    scaled = scale_meal(BASE_MEAL, 1.0)
    assert scaled["effective_calories"] == 400
    assert scaled["effective_carbs_g"] == 50.0


def test_scale_meal_one_and_half() -> None:
    scaled = scale_meal(BASE_MEAL, 1.5)
    assert scaled["effective_calories"] == 600
    assert scaled["effective_fat_g"] == 15.0
    assert scaled["ingredients"][0]["quantity"] == 150.0


def test_scale_meal_three() -> None:
    scaled = scale_meal(BASE_MEAL, 3.0)
    assert scaled["effective_calories"] == 1200
    assert scaled["effective_protein_g"] == 60.0
    assert scaled["ingredients"][0]["quantity"] == 300.0
