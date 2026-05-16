import type { DietMeal } from '../pages/DietPlanReview';

export default function MealEditModal({ meal, onClose, onRegenerate }: { meal: DietMeal | null; onClose: () => void; onRegenerate: () => void }) {
  if (!meal) return null;
  return (
    <div className="modal-backdrop">
      <div className="checkout-summary modal">
        <h2>Edit Meal</h2>
        <label>Meal name<input defaultValue={meal.meal_name} /></label>
        <button className="button-buy" onClick={onRegenerate}>Regenerate</button>
        <button className="button-ghost" onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
}
