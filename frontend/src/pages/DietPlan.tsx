import { Printer } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import MealDetailPanel from '../components/MealDetailPanel';
import WeekCalendar from '../components/WeekCalendar';
import { api } from '../lib/api';
import type { DietMeal } from './DietPlanReview';

type DietPlanResponse = { id: string; status: string; meals: DietMeal[] };

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

  // Auto-print when opened from the Plans page with ?print=1
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
      <section className="content">
        <div className="dashboard-hero">
          <div><span className="badge badge-success">Approved</span><h1>Diet Plan</h1></div>
          <button className="btn-icon-sm" style={{ fontSize: 13, padding: '8px 16px' }} onClick={() => window.print()}>
            <Printer size={15} /> Print / Save as PDF
          </button>
        </div>

        <div className="week-tabs">
          {Array.from({ length: numWeeks }, (_, i) => i + 1).map((w) => (
            <button key={w} className={week === w ? 'pill-tab active' : 'pill-tab'} onClick={() => setWeek(w)}>
              Week {w}
            </button>
          ))}
        </div>

        {plan && (
          <WeekCalendar
            meals={plan.meals}
            week={week}
            onMealClick={(meal) => { setSelected(meal); setMultiplier(meal.serving_multiplier || 1); }}
          />
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
