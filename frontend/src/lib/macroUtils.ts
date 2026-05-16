export type MealIngredient = { name: string; quantity: number; unit: string };
export type MealForScaling = {
  base_calories: number;
  base_protein_g: number;
  base_fat_g: number;
  base_carbs_g: number;
  ingredients: MealIngredient[];
};

export function scaleMeal<T extends MealForScaling>(meal: T, multiplier: number) {
  return {
    ...meal,
    serving_multiplier: multiplier,
    effective_calories: Math.round(meal.base_calories * multiplier),
    effective_protein_g: +(meal.base_protein_g * multiplier).toFixed(1),
    effective_fat_g: +(meal.base_fat_g * multiplier).toFixed(1),
    effective_carbs_g: +(meal.base_carbs_g * multiplier).toFixed(1),
    ingredients: meal.ingredients.map((ingredient) => ({
      ...ingredient,
      quantity: +(ingredient.quantity * multiplier).toFixed(1)
    }))
  };
}
