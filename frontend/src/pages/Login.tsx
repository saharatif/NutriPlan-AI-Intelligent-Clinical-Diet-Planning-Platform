import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

export default function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const signUp = useAuthStore((state) => state.signUp);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [clinic, setClinic] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === 'signup') {
        await signUp(email, password, name, clinic);
      } else {
        await login(email, password);
      }
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-screen">
      <section className="auth-showcase" aria-hidden="true">
        <div className="auth-showcase-copy">
          <span className="badge badge-warning">Clinical workspace</span>
          <h1>NutriPlan AI</h1>
        </div>
      </section>
      <section className="checkout-summary login-panel">
        <form className="form-grid" onSubmit={onSubmit}>
          <div className="form-heading">
            <span className="eyebrow">Doctor access</span>
            <h2>{mode === 'signup' ? 'Create your account' : 'Welcome back'}</h2>
          </div>
          <div className="segmented" role="tablist" aria-label="Authentication mode">
            <button type="button" className={mode === 'signin' ? 'active' : ''} onClick={() => setMode('signin')}>Sign in</button>
            <button type="button" className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Sign up</button>
          </div>
          {mode === 'signup' && (
            <div className="field-pair">
              <label>Name<input value={name} onChange={(e) => setName(e.target.value)} required /></label>
              <label>Clinic<input value={clinic} onChange={(e) => setClinic(e.target.value)} required /></label>
            </div>
          )}
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required /></label>
          <label>Password<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required /></label>
          {error && <p className="error">{error}</p>}
          <button className="button-primary" type="submit" disabled={submitting}>
            {submitting ? 'Please wait…' : mode === 'signup' ? 'Create account' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
