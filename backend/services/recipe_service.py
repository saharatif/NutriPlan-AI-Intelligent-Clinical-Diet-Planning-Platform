import httpx

THEMEALDB_SEARCH = "https://www.themealdb.com/api/json/v1/1/search.php"

SAFE_INGREDIENTS = [
    "oats", "quinoa", "brown rice", "lentils", "chickpeas", "spinach", "broccoli", "carrot",
    "cucumber", "tomato", "avocado", "olive oil", "salmon", "chicken breast", "turkey",
    "tofu-free tempeh alternative", "berries", "apple", "chia seeds", "sweet potato",
    "cauliflower", "zucchini", "beans", "herbs", "lemon", "pumpkin seeds", "whole grain wrap",
]


class RecipeService:
    def enrich(self, meal: dict, sequence: int) -> dict:
        """Add deterministic macro values and ingredients. recipe_url is left None
        and populated asynchronously via lookup_recipe_url() when a network call
        is available."""
        ingredient_a = SAFE_INGREDIENTS[sequence % len(SAFE_INGREDIENTS)]
        ingredient_b = SAFE_INGREDIENTS[(sequence + 7) % len(SAFE_INGREDIENTS)]
        ingredient_c = SAFE_INGREDIENTS[(sequence + 13) % len(SAFE_INGREDIENTS)]
        base_calories = 330 + (sequence % 9) * 35
        return {
            **meal,
            "base_calories": base_calories,
            "base_protein_g": round(18 + (sequence % 7) * 2.4, 1),
            "base_fat_g": round(9 + (sequence % 5) * 1.7, 1),
            "base_carbs_g": round(36 + (sequence % 8) * 3.1, 1),
            "ingredients": [
                {"name": ingredient_a, "quantity": 1.0, "unit": "cup"},
                {"name": ingredient_b, "quantity": 120.0, "unit": "g"},
                {"name": ingredient_c, "quantity": 1.0, "unit": "tbsp"},
            ],
            "recipe_url": meal.get("recipe_url"),  # preserve if already set (e.g. from OpenAI)
        }

    async def lookup_recipe_url(self, meal_name: str) -> str | None:
        """
        Query TheMealDB for a real recipe URL matching the meal name.
        Tries the most descriptive word in the name first, then falls back
        to shorter candidates. Returns None if no match is found.

        TheMealDB is free, requires no API key, and returns real recipe pages.
        """
        candidates = [w for w in meal_name.split() if len(w) > 4]
        candidates = candidates or meal_name.split()[:1]

        async with httpx.AsyncClient(timeout=5) as client:
            for word in candidates:
                try:
                    response = await client.get(THEMEALDB_SEARCH, params={"s": word})
                    if response.status_code != 200:
                        continue
                    meals = response.json().get("meals") or []
                    if meals:
                        meal_id = meals[0]["idMeal"]
                        return f"https://www.themealdb.com/meal/{meal_id}"
                except httpx.RequestError:
                    continue
        return None
