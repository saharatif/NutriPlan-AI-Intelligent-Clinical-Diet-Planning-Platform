import MealCard from './MealCard';
import type { DietMeal } from '../pages/DietPlanReview';
import { Fragment } from 'react';

const days = [1, 2, 3, 4, 5, 6, 7];
const slots = ['Breakfast', 'Lunch', 'Snack', 'Dinner'];

export default function WeekCalendar({ meals, week, onMealClick }: { meals: DietMeal[]; week: number; onMealClick: (meal: DietMeal) => void }) {
  return (
    <div className="calendar-grid">
      <div className="calendar-corner">Week {week}</div>
      {days.map((day) => <div className="calendar-head" key={day}>Day {day}</div>)}
      {slots.map((slot) => (
        <Fragment key={slot}>
          <div className="calendar-slot" key={`${slot}-label`}>{slot}</div>
          {days.map((day) => {
            const meal = meals.find((item) => item.week === week && item.day === day && item.meal_slot === slot);
            return <div className="calendar-cell" key={`${slot}-${day}`}>{meal && <MealCard meal={meal} onClick={() => onMealClick(meal)} />}</div>;
          })}
        </Fragment>
      ))}
    </div>
  );
}
