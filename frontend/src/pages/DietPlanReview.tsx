import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import DailyNutritionChart from '../components/DailyNutritionChart';
import MealDetailPanel from '../components/MealDetailPanel';
import WeekCalendar from '../components/WeekCalendar';
import { api } from '../lib/api';

export type DietMeal = {
  id: string;
  week: number;
  day: number;
  meal_slot: string;
  meal_name: string;
  base_calories: number;
  base_protein_g: number;
  base_fat_g: number;
  base_carbs_g: number;
  ingredients: Array<{ name: string; quantity: number; unit: string }>;
  recipe_url?: string | null;
  clinical_note?: string | null;
  serving_multiplier: number;
};

type DietPlanResponse = { id: string; status: string; meals: DietMeal[] };

function weekCalories(meals: DietMeal[], week: number) {
  return meals.filter((m) => m.week === week).reduce((s, m) => s + m.base_calories, 0);
}

export default function DietPlanReview() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<DietPlanResponse | null>(null);
  const [week, setWeek] = useState(1);
  const [selected, setSelected] = useState<DietMeal | null>(null);
  const [multiplier, setMultiplier] = useState(1);

  const numWeeks = plan
    ? Math.max(...plan.meals.map((m) => m.week))
    : 4;

  async function load() {
    if (!planId) return;
    const response = await api.get<DietPlanResponse>(`/diet-plans/${planId}`);
    setPlan(response.data);
  }

  async function regenerate(meal: DietMeal) {
    if (!planId) return;
    const response = await api.post<DietMeal>(`/diet-plans/${planId}/meals/${meal.id}/regenerate`);
    setSelected(response.data);
    await load();
  }

  async function approve() {
    if (!planId) return;
    await api.post(`/diet-plans/${planId}/approve`);
    navigate(`/diet-plans/${planId}`);
  }

  useEffect(() => { void load(); }, [planId]);

  return (
    <main className="app-shell">
      {/* Sticky draft banner */}
      <div className="draft-banner">
        <div className="draft-banner-inner">
          <div className="draft-banner-left">
            <span className="draft-banner-dot" />
            <span className="draft-banner-text">Draft — review all meals before approving</span>
          </div>
          <button className="draft-banner-approve" onClick={() => void approve()}>
            Approve Plan
          </button>
        </div>
      </div>

      <section className="content">
        <div className="page-title" style={{ paddingTop: 16 }}>
          <h1>Plan Review</h1>
        </div>

        {/* Week tabs with calorie totals */}
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
                  <span className="week-tab-badge">{Math.round(kcal / 1000 * 10) / 10}k kcal</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Calendar grid */}
        {plan && (
          <WeekCalendar
            meals={plan.meals}
            week={week}
            onMealClick={(meal) => { setSelected(meal); setMultiplier(meal.serving_multiplier || 1); }}
            onMealSwap={(meal) => void regenerate(meal)}
          />
        )}

        {/* Daily nutrition chart */}
        {plan && plan.meals.length > 0 && (
          <DailyNutritionChart meals={plan.meals} week={week} />
        )}

        <MealDetailPanel
          meal={selected}
          multiplier={multiplier}
          onMultiplier={setMultiplier}
          onRegenerate={() => selected && void regenerate(selected)}
          onClose={() => setSelected(null)}
        />
      </section>
    </main>
  );
}
