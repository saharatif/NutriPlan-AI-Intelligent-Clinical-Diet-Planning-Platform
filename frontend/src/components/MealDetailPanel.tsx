import MacroSlider from './MacroSlider';
import { scaleMeal } from '../lib/macroUtils';
import type { DietMeal } from '../pages/DietPlanReview';

export default function MealDetailPanel({
  meal,
  multiplier,
  onMultiplier,
  onRegenerate,
  onClose
}: {
  meal: DietMeal | null;
  multiplier: number;
  onMultiplier: (value: number) => void;
  onRegenerate: () => void;
  onClose: () => void;
}) {
  if (!meal) return null;
  const scaled = scaleMeal(meal, multiplier);
  return (
    <aside className="detail-panel">
      <button className="button-ghost" onClick={onClose}>Close</button>
      <h2>{meal.meal_name}</h2>
      <p>{meal.clinical_note}</p>
      <MacroSlider value={multiplier} onChange={onMultiplier} />
      <div className="macro-row">
        <span>{scaled.effective_calories} kcal</span>
        <span>P {scaled.effective_protein_g}</span>
        <span>F {scaled.effective_fat_g}</span>
        <span>C {scaled.effective_carbs_g}</span>
      </div>
      <ul>{scaled.ingredients.map((ingredient) => <li key={ingredient.name}>{ingredient.quantity} {ingredient.unit} {ingredient.name}</li>)}</ul>
      {meal.recipe_url && <a className="table-link" href={meal.recipe_url} target="_blank" rel="noreferrer">Recipe</a>}
      <button className="button-buy" onClick={onRegenerate}>Regenerate This Meal</button>
    </aside>
  );
}
