import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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

export default function DietPlanReview() {
  const { planId } = useParams();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<DietPlanResponse | null>(null);
  const [week, setWeek] = useState(1);
  const [selected, setSelected] = useState<DietMeal | null>(null);
  const [multiplier, setMultiplier] = useState(1);

  async function load() {
    if (!planId) return;
    const response = await api.get<DietPlanResponse>(`/diet-plans/${planId}`);
    setPlan(response.data);
  }

  async function regenerate() {
    if (!planId || !selected) return;
    const response = await api.post<DietMeal>(`/diet-plans/${planId}/meals/${selected.id}/regenerate`);
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
      <section className="content">
        <div className="dashboard-hero"><div><span className="badge badge-warning">Draft review</span><h1>Plan Review</h1></div><button className="button-buy" onClick={() => void approve()}>Approve Plan</button></div>
        <div className="week-tabs">{[1, 2, 3, 4].map((item) => <button className={week === item ? 'pill-tab active' : 'pill-tab'} onClick={() => setWeek(item)} key={item}>Week {item}</button>)}</div>
        {plan && <WeekCalendar meals={plan.meals} week={week} onMealClick={(meal) => { setSelected(meal); setMultiplier(meal.serving_multiplier || 1); }} />}
        <MealDetailPanel meal={selected} multiplier={multiplier} onMultiplier={setMultiplier} onRegenerate={() => void regenerate()} onClose={() => setSelected(null)} />
      </section>
    </main>
  );
}
