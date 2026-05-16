import type { DietMeal } from '../pages/DietPlanReview';

export default function MealCard({ meal, onClick }: { meal: DietMeal; onClick: () => void }) {
  return (
    <button type="button" className={`meal-card ${meal.meal_slot.toLowerCase()}`} onClick={onClick}>
      <strong>{meal.meal_name}</strong>
      <span>{meal.base_calories} kcal</span>
      <small>P {meal.base_protein_g} / F {meal.base_fat_g} / C {meal.base_carbs_g}</small>
    </button>
  );
}
