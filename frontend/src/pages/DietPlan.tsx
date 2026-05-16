import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import MealDetailPanel from '../components/MealDetailPanel';
import WeekCalendar from '../components/WeekCalendar';
import { api } from '../lib/api';
import type { DietMeal } from './DietPlanReview';

type DietPlanResponse = { id: string; status: string; meals: DietMeal[] };

export default function DietPlan() {
  const { planId } = useParams();
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

  async function exportPdf() {
    if (!planId) return;
    const response = await api.post<{ url: string }>(`/diet-plans/${planId}/export/pdf`);
    window.location.href = response.data.url;
  }

  useEffect(() => { void load(); }, [planId]);

  return (
    <main className="app-shell">
      <section className="content">
        <div className="dashboard-hero"><div><span className="badge badge-success">Approved</span><h1>Diet Plan</h1></div><button className="button-buy" onClick={() => void exportPdf()}>Export PDF</button></div>
        <div className="week-tabs">{[1, 2, 3, 4].map((item) => <button className={week === item ? 'pill-tab active' : 'pill-tab'} onClick={() => setWeek(item)} key={item}>Week {item}</button>)}</div>
        {plan && <WeekCalendar meals={plan.meals} week={week} onMealClick={(meal) => { setSelected(meal); setMultiplier(meal.serving_multiplier || 1); }} />}
        <MealDetailPanel meal={selected} multiplier={multiplier} onMultiplier={(value) => void persistMultiplier(value)} onRegenerate={() => undefined} onClose={() => setSelected(null)} />
      </section>
    </main>
  );
}
