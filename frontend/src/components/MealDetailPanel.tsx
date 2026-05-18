import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { scaleMeal } from '../lib/macroUtils';
import type { DietMeal } from '../pages/DietPlanReview';
import MacroSlider from './MacroSlider';

function RecipeSteps({ meal }: { meal: DietMeal }) {
  const [steps, setSteps] = useState<string[]>(meal.recipe_steps ?? []);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Reset when a different meal is selected
    setSteps(meal.recipe_steps ?? []);
  }, [meal.id]);

  useEffect(() => {
    // Auto-fetch if steps not yet generated
    if (steps.length > 0 || !meal.diet_plan_id) return;
    setLoading(true);
    api.get<{ steps: string[] }>(`/diet-plans/${meal.diet_plan_id}/meals/${meal.id}/steps`)
      .then((r) => setSteps(r.data.steps))
      .catch(() => setSteps(['Unable to load recipe steps — please try again.']))
      .finally(() => setLoading(false));
  }, [meal.id, steps.length]);

  return (
    <div className="recipe-steps">
      <h3>How to make it</h3>
      {loading && <p className="steps-loading">Generating recipe steps…</p>}
      {!loading && steps.length > 0 && (
        <ol className="steps-list">
          {steps.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default function MealDetailPanel({
  meal,
  multiplier,
  onMultiplier,
  onRegenerate,
  onClose,
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

      <div>
        <h2>{meal.meal_name}</h2>
        {meal.clinical_note && <p style={{ color: 'var(--slate)', fontSize: 13, marginTop: 4 }}>{meal.clinical_note}</p>}
      </div>

      <MacroSlider value={multiplier} onChange={onMultiplier} />

      <div className="macro-row">
        <span>{scaled.effective_calories} kcal</span>
        <span>P {scaled.effective_protein_g}g</span>
        <span>F {scaled.effective_fat_g}g</span>
        <span>C {scaled.effective_carbs_g}g</span>
      </div>

      <div>
        <h3 style={{ fontSize: 12, fontWeight: 600, color: 'var(--slate)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>Ingredients</h3>
        <ul className="ingredients-list">
          {scaled.ingredients.map((ingredient) => (
            <li key={ingredient.name}>
              <span className="ingredient-qty">{ingredient.quantity} {ingredient.unit}</span>
              {ingredient.name}
            </li>
          ))}
        </ul>
      </div>

      <RecipeSteps meal={meal} />

      {meal.recipe_url && (
        <a className="table-link" href={meal.recipe_url} target="_blank" rel="noreferrer">
          View full recipe →
        </a>
      )}

      <button className="button-buy" onClick={onRegenerate}>Regenerate This Meal</button>
    </aside>
  );
}
