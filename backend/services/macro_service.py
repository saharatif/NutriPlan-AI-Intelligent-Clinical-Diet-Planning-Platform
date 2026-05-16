from copy import deepcopy


def scale_meal(meal: dict, multiplier: float) -> dict:
    scaled = deepcopy(meal)
    scaled["serving_multiplier"] = multiplier
    scaled["effective_calories"] = round(float(meal["base_calories"]) * multiplier)
    scaled["effective_protein_g"] = round(float(meal["base_protein_g"]) * multiplier, 1)
    scaled["effective_fat_g"] = round(float(meal["base_fat_g"]) * multiplier, 1)
    scaled["effective_carbs_g"] = round(float(meal["base_carbs_g"]) * multiplier, 1)
    scaled["ingredients"] = [
        {**ingredient, "quantity": round(float(ingredient["quantity"]) * multiplier, 1)}
        for ingredient in meal.get("ingredients", [])
    ]
    return scaled
