import { useState } from 'react';
import type { DietMeal } from '../pages/DietPlanReview';

function MacroBadges({ p, f, c }: { p: number; f: number; c: number }) {
  return (
    <div className="macro-badges">
      <span className="macro-badge macro-p">P {p}g</span>
      <span className="macro-badge macro-f">F {f}g</span>
      <span className="macro-badge macro-c">C {c}g</span>
    </div>
  );
}

export default function MealCard({
  meal,
  onClick,
  onSwap,
}: {
  meal: DietMeal;
  onClick: () => void;
  onSwap?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const slotClass = meal.meal_slot.toLowerCase();
  const topIngredients = meal.ingredients?.slice(0, 3).map((i) => i.name).join(', ');

  return (
    <div
      className={`meal-card-wrap ${slotClass}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <button
        type="button"
        className={`meal-card ${slotClass}`}
        onClick={onClick}
        title={meal.meal_name}
      >
        <strong>{meal.meal_name}</strong>
        <span>{meal.base_calories} kcal</span>
        <MacroBadges p={meal.base_protein_g} f={meal.base_fat_g} c={meal.base_carbs_g} />
      </button>

      {hovered && (
        <div className="meal-hover-card">
          <div className="meal-hover-name">{meal.meal_name}</div>
          {topIngredients && (
            <div className="meal-hover-ingredients">{topIngredients}{meal.ingredients?.length > 3 ? ` +${meal.ingredients.length - 3} more` : ''}</div>
          )}
          <div className="meal-hover-actions">
            <button type="button" className="meal-hover-btn" onClick={onClick}>View details</button>
            {onSwap && <button type="button" className="meal-hover-btn meal-hover-btn-swap" onClick={onSwap}>Swap meal</button>}
          </div>
        </div>
      )}
    </div>
  );
}
