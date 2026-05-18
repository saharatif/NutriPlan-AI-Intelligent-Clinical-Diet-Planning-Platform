import { Printer } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import DailyNutritionChart from '../components/DailyNutritionChart';
import MealDetailPanel from '../components/MealDetailPanel';
import WeekCalendar from '../components/WeekCalendar';
import { api } from '../lib/api';
import type { DietMeal } from './DietPlanReview';

type DietPlanResponse = { id: string; status: string; meals: DietMeal[] };

function weekCalories(meals: DietMeal[], w: number) {
  return meals.filter((m) => m.week === w).reduce((s, m) => s + m.base_calories, 0);
}

export default function DietPlan() {
  const { planId } = useParams();
  const [searchParams] = useSearchParams();
  const [plan, setPlan] = useState<DietPlanResponse | null>(null);
  const [week, setWeek] = useState(1);
  const [selected, setSelected] = useState<DietMeal | null>(null);
  const [multiplier, setMultiplier] = useState(1);

  async function load() {
    if (!planId) return;
    const response = await api.get<DietPlanResponse>(`/diet-plans/${planId}`);
    setPlan(response.data);
  }

  async function persistMultiplier(value: number) {
    setMultiplier(value);
    if (planId && selected) await api.patch(`/diet-plans/${planId}/meals/${selected.id}`, { serving_multiplier: value });
  }

  useEffect(() => { void load(); }, [planId]);

  useEffect(() => {
    if (plan && searchParams.get('print') === '1') {
      setTimeout(() => window.print(), 500);
    }
  }, [plan, searchParams]);

  const numWeeks = plan && plan.meals.length > 0
    ? Math.max(...plan.meals.map((m) => m.week))
    : 0;

  return (
    <main className="app-shell">
      {/* Sticky page header */}
      <header className="plan-sticky-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="badge badge-success">Approved</span>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Diet Plan</h1>
        </div>
        <button className="button-ghost" style={{ gap: 6, minHeight: 36 }} onClick={() => window.print()}>
          <Printer size={14} /> Print / Save as PDF
        </button>
      </header>

      <section className="content">
        {/* Week tabs with calorie badges */}
        <div className="week-tabs">
          {Array.from({ length: numWeeks }, (_, i) => i + 1).map((w) => {
            const kcal = plan ? weekCalories(plan.meals, w) : null;
            return (
              <button
                key={w}
                className={week === w ? 'pill-tab active' : 'pill-tab'}
                onClick={() => setWeek(w)}
              >
                Week {w}
                {kcal !== null && (
                  <span className="week-tab-badge">
                    {(kcal / 1000).toFixed(1)}k kcal
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Calendar */}
        {plan && (
          <WeekCalendar
            meals={plan.meals}
            week={week}
            onMealClick={(meal) => { setSelected(meal); setMultiplier(meal.serving_multiplier || 1); }}
          />
        )}

        {/* Daily Nutrition Chart */}
        {plan && plan.meals.length > 0 && (
          <DailyNutritionChart meals={plan.meals} week={week} />
        )}

        <MealDetailPanel
          meal={selected}
          multiplier={multiplier}
          onMultiplier={(value) => void persistMultiplier(value)}
          onRegenerate={() => undefined}
          onClose={() => setSelected(null)}
        />
      </section>
    </main>
  );
}
