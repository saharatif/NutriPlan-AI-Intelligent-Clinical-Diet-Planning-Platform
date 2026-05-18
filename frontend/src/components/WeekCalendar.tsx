import { Fragment } from 'react';
import MealCard from './MealCard';
import type { DietMeal } from '../pages/DietPlanReview';

const days = [1, 2, 3, 4, 5, 6, 7];
const slots = ['Breakfast', 'Lunch', 'Snack', 'Dinner'];

export default function WeekCalendar({
  meals,
  week,
  onMealClick,
  onMealSwap,
}: {
  meals: DietMeal[];
  week: number;
  onMealClick: (meal: DietMeal) => void;
  onMealSwap?: (meal: DietMeal) => void;
}) {
  const weekMeals = meals.filter((m) => m.week === week);

  const dayTotals = days.map((day) => {
    const dayMeals = weekMeals.filter((m) => m.day === day);
    return {
      calories: dayMeals.reduce((s, m) => s + m.base_calories, 0),
      protein: dayMeals.reduce((s, m) => s + m.base_protein_g, 0),
      fat: dayMeals.reduce((s, m) => s + m.base_fat_g, 0),
      carbs: dayMeals.reduce((s, m) => s + m.base_carbs_g, 0),
    };
  });

  return (
    <div className="calendar-grid">
      <div className="calendar-corner">Week {week}</div>
      {days.map((day) => <div className="calendar-head" key={day}>Day {day}</div>)}

      {slots.map((slot) => (
        <Fragment key={slot}>
          <div className={`calendar-slot slot-${slot.toLowerCase()}`}>{slot}</div>
          {days.map((day) => {
            const meal = weekMeals.find((m) => m.day === day && m.meal_slot === slot);
            return (
              <div className="calendar-cell" key={`${slot}-${day}`}>
                {meal && (
                  <MealCard
                    meal={meal}
                    onClick={() => onMealClick(meal)}
                    onSwap={onMealSwap ? () => onMealSwap(meal) : undefined}
                  />
                )}
              </div>
            );
          })}
        </Fragment>
      ))}

      {/* Daily totals row */}
      <div className="calendar-totals-label">Daily total</div>
      {dayTotals.map((t, i) => (
        <div className="calendar-totals-cell" key={i}>
          <span className="totals-kcal">{t.calories} kcal</span>
          <div className="totals-macros">
            <span className="macro-badge macro-p">P {Math.round(t.protein)}g</span>
            <span className="macro-badge macro-f">F {Math.round(t.fat)}g</span>
            <span className="macro-badge macro-c">C {Math.round(t.carbs)}g</span>
          </div>
        </div>
      ))}
    </div>
  );
}
