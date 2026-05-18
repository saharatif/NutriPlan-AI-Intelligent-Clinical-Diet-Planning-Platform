import type { DietMeal } from '../pages/DietPlanReview';

const CHART_H = 120;
const BAR_W = 28;
const GAP = 14;
const DAYS = [1, 2, 3, 4, 5, 6, 7];

export default function DailyNutritionChart({ meals, week }: { meals: DietMeal[]; week: number }) {
  const weekMeals = meals.filter((m) => m.week === week);

  const dayData = DAYS.map((day) => {
    const dm = weekMeals.filter((m) => m.day === day);
    return {
      day,
      calories: dm.reduce((s, m) => s + m.base_calories, 0),
      protein: dm.reduce((s, m) => s + m.base_protein_g, 0),
      fat: dm.reduce((s, m) => s + m.base_fat_g, 0),
      carbs: dm.reduce((s, m) => s + m.base_carbs_g, 0),
    };
  });

  const maxCal = Math.max(...dayData.map((d) => d.calories), 1);
  const svgW = DAYS.length * (BAR_W + GAP) + GAP;

  return (
    <div className="daily-chart-wrap">
      <div className="daily-chart-title">Daily calorie breakdown — Week {week}</div>
      <svg width={svgW} height={CHART_H + 40} className="daily-chart-svg">
        {dayData.map((d, i) => {
          const x = GAP + i * (BAR_W + GAP);
          const barH = maxCal > 0 ? (d.calories / maxCal) * CHART_H : 0;
          const y = CHART_H - barH;

          // Stacked: protein / fat / carbs (roughly proportional within total kcal)
          const total = d.protein * 4 + d.fat * 9 + d.carbs * 4 || 1;
          const pH = (d.protein * 4 / total) * barH;
          const fH = (d.fat * 9 / total) * barH;
          const cH = (d.carbs * 4 / total) * barH;

          return (
            <g key={d.day}>
              {/* carbs (bottom) */}
              <rect x={x} y={y} width={BAR_W} height={cH} fill="#059669" rx={d.day === 1 ? 3 : 0} />
              {/* fat */}
              <rect x={x} y={y + cH} width={BAR_W} height={fH} fill="#d97706" />
              {/* protein (top) */}
              <rect x={x} y={y + cH + fH} width={BAR_W} height={pH} fill="#2563eb" rx={2} />
              {/* calorie label */}
              <text x={x + BAR_W / 2} y={y - 4} textAnchor="middle" fontSize={9} fill="var(--slate)">
                {d.calories}
              </text>
              {/* day label */}
              <text x={x + BAR_W / 2} y={CHART_H + 14} textAnchor="middle" fontSize={10} fill="var(--slate)">
                D{d.day}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="daily-chart-legend">
        <span className="legend-dot" style={{ background: '#2563eb' }} />Protein
        <span className="legend-dot" style={{ background: '#d97706', marginLeft: 10 }} />Fat
        <span className="legend-dot" style={{ background: '#059669', marginLeft: 10 }} />Carbs
      </div>
    </div>
  );
}
