import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';

type StatusResponse = { status: string; plan_id: string | null };

const POLL_INTERVAL_MS = 2500;
const POLL_MAX_ATTEMPTS = 120; // 5 minutes before giving up

export default function GenerateDietPlan() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [planType, setPlanType] = useState('4-week');
  const [selectedFavourites, setSelectedFavourites] = useState<string[]>(['dal', 'oatmeal', 'salmon']);
  const [allergens, setAllergens] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');
  const [statusLabel, setStatusLabel] = useState('Ready');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!patientId) return;
    void api.get<{ allergens: Array<{ name: string }> }>(`/patients/${patientId}`)
      .then((r) => setAllergens(r.data.allergens.map((a) => a.name.toLowerCase())));
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [patientId]);

  async function generate() {
    if (!patientId || status === 'generating') return;
    setStatus('generating');
    setStatusLabel('Queuing generation…');

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
        const { status: taskStatus, plan_id: planId } = poll.data;

        if (taskStatus === 'success' && planId) {
          clearInterval(pollRef.current!);
          setStatus('complete');
          setStatusLabel('Complete');
          navigate(`/diet-plans/${planId}/review`);
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

  const favouriteOptions = ['dal', 'oatmeal', 'salmon', 'milk smoothie', 'peanut chutney', 'soy bowl'];
  const progress = status === 'complete' ? 100 : status === 'generating' ? 65 : status === 'error' ? 0 : 10;

  return (
    <main className="app-shell">
      <section className="content narrow">
        <div className="page-title">
          <span className={`badge ${status === 'error' ? 'badge-warning' : status === 'complete' ? 'badge-success' : 'badge-warning'}`}>
            {statusLabel}
          </span>
          <h1>Generate Plan</h1>
        </div>
        <div className="checkout-summary form-grid">
          <label>Plan type
            <select value={planType} onChange={(e) => setPlanType(e.target.value)} disabled={status === 'generating'}>
              <option>1-week</option>
              <option>4-week</option>
            </select>
          </label>
          <div className="form-section">
            <div className="section-kicker">Favourite foods</div>
            <div className="chip-row">
              {favouriteOptions.map((food) => {
                const blocked = allergens.some((a) => food.includes(a));
                const selected = selectedFavourites.includes(food);
                return (
                  <button
                    type="button"
                    className={selected ? 'pill-tab active' : 'pill-tab'}
                    disabled={blocked || status === 'generating'}
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
          <div className="progress-bar"><span style={{ width: `${progress}%` }} /></div>
          <button
            className="button-primary"
            disabled={status === 'generating'}
            onClick={() => void generate()}
          >
            {status === 'generating' ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </section>
    </main>
  );
}
