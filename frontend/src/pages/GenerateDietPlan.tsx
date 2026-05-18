import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';

type StatusResponse = { status: string; plan_id: string | null; progress: number };

const POLL_INTERVAL_MS = 2500;
const POLL_MAX_ATTEMPTS = 200;

const CIRCUMFERENCE = 2 * Math.PI * 36; // r=36

function ProgressDonut({ progress, weeks }: { progress: number; weeks: number }) {
  const offset = CIRCUMFERENCE * (1 - progress / 100);
  const estimatedSecs = weeks === 2 ? 200 : 380;
  const label = progress === 0
    ? `~${Math.round(estimatedSecs / 60)}m`
    : progress === 100
    ? 'Done'
    : `${progress}%`;

  return (
    <div className="donut-wrap">
      <svg width="88" height="88" className="donut-svg">
        <circle cx="44" cy="44" r="36" className="donut-track" />
        <circle
          cx="44" cy="44" r="36"
          className="donut-fill"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="donut-label">{label}</span>
    </div>
  );
}

export default function GenerateDietPlan() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [weeks, setWeeks] = useState<2 | 4>(4);
  const [favouriteOptions, setFavouriteOptions] = useState<string[]>([]);
  const [selectedFavourites, setSelectedFavourites] = useState<string[]>([]);
  const [allergens, setAllergens] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');
  const [statusLabel, setStatusLabel] = useState('Ready to generate');
  const [progress, setProgress] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!patientId) return;
    void api.get<{
      allergens: Array<{ name: string }>;
      favourite_foods: Array<{ name: string }>;
    }>(`/patients/${patientId}`).then((r) => {
      const allergensLower = r.data.allergens.map((a) => a.name.toLowerCase());
      setAllergens(allergensLower);

      const foods = r.data.favourite_foods.map((f) => f.name.toLowerCase());
      setFavouriteOptions(foods);
      // Pre-select all favourites that aren't blocked by allergens
      const safe = foods.filter(
        (food) => !allergensLower.some((a) => food.includes(a) || a.includes(food.split(' ')[0]))
      );
      setSelectedFavourites(safe);
    });
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [patientId]);

  async function generate() {
    if (!patientId || status === 'generating') return;
    setStatus('generating');
    setProgress(0);
    setStatusLabel('Queuing…');

    const planType = `${weeks}-week`;
    const taskResponse = await api.post<{ task_id: string }>(
      `/patients/${patientId}/diet-plans/generate`,
      { plan_type: planType, selected_favourites: selectedFavourites }
    );
    const taskId = taskResponse.data.task_id;
    setStatusLabel('Generating plan…');

    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts += 1;
      try {
        const poll = await api.get<StatusResponse>(
          `/patients/${patientId}/diet-plans/generate/${taskId}/status`
        );
        const { status: taskStatus, plan_id: planId, progress: pct } = poll.data;

        if (taskStatus === 'generating' || taskStatus === 'started') {
          setProgress(pct ?? 0);
        } else if (taskStatus === 'success' && planId) {
          clearInterval(pollRef.current!);
          setProgress(100);
          setStatus('complete');
          setStatusLabel('Complete!');
          setTimeout(() => navigate(`/diet-plans/${planId}/review`), 600);
        } else if (taskStatus === 'failure') {
          clearInterval(pollRef.current!);
          setStatus('error');
          setStatusLabel('Generation failed — please try again');
        } else if (attempts >= POLL_MAX_ATTEMPTS) {
          clearInterval(pollRef.current!);
          setStatus('error');
          setStatusLabel('Timed out — please try again');
        }
      } catch {
        // Network blip — keep polling
      }
    }, POLL_INTERVAL_MS);
  }

  const isGenerating = status === 'generating';

  return (
    <main className="app-shell">
      <section className="content narrow">
        <div className="page-title">
          <h1>Generate Diet Plan</h1>
        </div>

        <div className="checkout-summary form-grid">
          {/* Week selector */}
          <div>
            <div className="section-kicker" style={{ marginBottom: 8 }}>Plan duration</div>
            <div className="segmented" role="radiogroup" aria-label="Plan weeks">
              {([2, 4] as const).map((w) => (
                <button
                  key={w}
                  type="button"
                  className={weeks === w ? 'active' : ''}
                  disabled={isGenerating}
                  onClick={() => setWeeks(w)}
                >
                  {w} weeks
                </button>
              ))}
            </div>
            <p style={{ fontSize: 12, color: 'var(--slate)', marginTop: 6 }}>
              {weeks === 2 ? 'Approx. 3–4 min to generate' : 'Approx. 6–8 min to generate'}
            </p>
          </div>

          {/* Favourite foods */}
          <div className="form-section">
            <div className="section-kicker">Favourite foods</div>
            {favouriteOptions.length === 0 && (
              <p style={{ fontSize: 12, color: 'var(--slate)' }}>
                No favourite foods on this patient's profile — add them on the patient profile page to pre-populate this list.
              </p>
            )}
            <div className="chip-row">
              {favouriteOptions.map((food) => {
                const blocked = allergens.some((a) => food.includes(a) || a.includes(food.split(' ')[0]));
                const selected = selectedFavourites.includes(food);
                return (
                  <button
                    type="button"
                    className={selected ? 'pill-tab active' : 'pill-tab'}
                    disabled={blocked || isGenerating}
                    key={food}
                    onClick={() => setSelectedFavourites(
                      selected ? selectedFavourites.filter((f) => f !== food) : [...selectedFavourites, food]
                    )}
                  >
                    {food}{blocked ? ' (blocked)' : ''}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Progress donut */}
          {(isGenerating || status === 'complete') && (
            <div className="donut-section">
              <ProgressDonut progress={progress} weeks={weeks} />
              <div>
                <div className="donut-status-label">{statusLabel}</div>
                {isGenerating && (
                  <div className="donut-sublabel">
                    Generating {weeks * 7 * 4} meals with GPT-4o — please keep this tab open
                  </div>
                )}
              </div>
            </div>
          )}

          {status === 'error' && (
            <p className="error">{statusLabel}</p>
          )}

          <button
            className="button-primary"
            disabled={isGenerating}
            onClick={() => void generate()}
          >
            {isGenerating ? 'Generating…' : status === 'complete' ? 'Generate Again' : 'Generate Plan'}
          </button>
        </div>
      </section>
    </main>
  );
}
