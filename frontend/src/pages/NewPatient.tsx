import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePatientStore } from '../store/usePatientStore';

export default function NewPatient() {
  const navigate = useNavigate();
  const createPatient = usePatientStore((state) => state.createPatient);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [sex, setSex] = useState<'male' | 'female' | 'other' | ''>('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [condition, setCondition] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createPatient({
        first_name: firstName,
        last_name: lastName,
        ...(dateOfBirth ? { date_of_birth: dateOfBirth } : {}),
        ...(sex ? { sex } : {}),
        ...(heightCm ? { height_cm: Number(heightCm) } : {}),
        ...(weightKg ? { weight_kg: Number(weightKg) } : {}),
        conditions: condition ? [{ name: condition }] : [],
      });
      navigate('/');
    } catch {
      setError('Failed to create patient. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <strong>NutriPlan AI</strong>
          <span>Patient intake</span>
        </div>
        <Link className="button-ghost" to="/">Back</Link>
      </header>

      <section className="content narrow">
        <div className="page-title">
          <span className="badge badge-warning">Steps 1–2</span>
          <h1>New Patient</h1>
        </div>

        <form className="checkout-summary form-grid" onSubmit={onSubmit}>
          <section className="form-section">
            <div className="section-kicker">Basic info</div>
            <div className="field-pair">
              <label>First name<input value={firstName} onChange={(e) => setFirstName(e.target.value)} required /></label>
              <label>Last name<input value={lastName} onChange={(e) => setLastName(e.target.value)} required /></label>
            </div>
            <div className="field-pair three">
              <label>Date of birth<input value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} type="date" /></label>
              <label>Height<input value={heightCm} onChange={(e) => setHeightCm(e.target.value)} type="number" min="1" placeholder="cm" /></label>
              <label>Weight<input value={weightKg} onChange={(e) => setWeightKg(e.target.value)} type="number" min="1" placeholder="kg" /></label>
            </div>
            <div className="radio-row" role="group" aria-label="Sex">
              <button type="button" className={sex === 'female' ? 'radio-option selected' : 'radio-option'} onClick={() => setSex('female')}>Female</button>
              <button type="button" className={sex === 'male' ? 'radio-option selected' : 'radio-option'} onClick={() => setSex('male')}>Male</button>
              <button type="button" className={sex === 'other' ? 'radio-option selected' : 'radio-option'} onClick={() => setSex('other')}>Other</button>
            </div>
          </section>

          <section className="form-section">
            <div className="section-kicker">Medical conditions</div>
            <label>Condition<input value={condition} onChange={(e) => setCondition(e.target.value)} placeholder="Type 2 diabetes" /></label>
          </section>

          {error && <p className="error">{error}</p>}

          <button className="button-primary" type="submit" disabled={submitting}>
            {submitting ? 'Creating patient…' : 'Create patient'}
          </button>
        </form>
      </section>
    </main>
  );
}
