import { Printer } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';

type Plan = {
  id: string;
  patient_id: string;
  patient_code: string;
  patient_name: string;
  status: string;
  plan_type: string;
  approved_at: string | null;
  created_at: string;
};

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Plan[]>('/diet-plans')
      .then((r) => setPlans(r.data))
      .catch(() => setError('Failed to load plans'))
      .finally(() => setLoading(false));
  }, []);

  function openPrint(planId: string) {
    window.open(`/diet-plans/${planId}?print=1`, '_blank');
  }

  return (
    <div className="content">
      <div className="page-header">
        <div>
          <h1>Diet Plans</h1>
          <p style={{ color: 'var(--slate)', fontSize: 14, marginTop: 4 }}>
            {loading ? 'Loading…' : `${plans.length} approved plan${plans.length !== 1 ? 's' : ''}`}
          </p>
        </div>
      </div>

      <div className="data-panel">
        <div className="panel-header">
          <div>
            <h2>Approved plans</h2>
            <span>Plans are saved here after approval — print or save as PDF to share with patients</span>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <table>
          <thead>
            <tr>
              <th>Patient</th>
              <th>Code</th>
              <th>Type</th>
              <th>Approved</th>
              <th>Created</th>
              <th></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.id}>
                <td style={{ fontWeight: 500 }}>{plan.patient_name}</td>
                <td><span className="profile-chip">{plan.patient_code}</span></td>
                <td style={{ textTransform: 'capitalize' }}>
                  {plan.plan_type.replace('-', ' ')}
                </td>
                <td style={{ color: 'var(--slate)' }}>
                  {plan.approved_at ? new Date(plan.approved_at).toLocaleDateString() : '—'}
                </td>
                <td style={{ color: 'var(--slate)' }}>
                  {new Date(plan.created_at).toLocaleDateString()}
                </td>
                <td>
                  <Link className="table-link" to={`/diet-plans/${plan.id}`}>View →</Link>
                </td>
                <td>
                  <button
                    className="btn-icon-sm"
                    title="Print / Save as PDF"
                    onClick={() => openPrint(plan.id)}
                  >
                    <Printer size={13} /> PDF
                  </button>
                </td>
              </tr>
            ))}
            {!loading && plans.length === 0 && (
              <tr>
                <td colSpan={7} style={{ color: 'var(--slate)', textAlign: 'center', padding: '32px' }}>
                  No approved plans yet — approve a plan from the review screen to see it here
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
