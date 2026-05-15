import { ClipboardList, FileText, Plus, ShieldCheck, UserRound } from 'lucide-react';
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { usePatientStore } from '../store/usePatientStore';

export default function Dashboard() {
  const doctor = useAuthStore((state) => state.doctor);
  const logout = useAuthStore((state) => state.logout);
  const { patients, fetchPatients, loading, error } = usePatientStore();

  useEffect(() => {
    void fetchPatients();
  }, [fetchPatients]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <strong>NutriPlan AI</strong>
          <span>{doctor?.clinic ?? doctor?.name}</span>
        </div>
        <nav className="pill-nav" aria-label="Workspace">
          <Link className="pill-tab active" to="/">Patients</Link>
          <button className="pill-tab" disabled title="Available in Week 4">Plans</button>
          <button className="pill-tab" disabled title="Available in Week 4">Documents</button>
        </nav>
        <button className="button-ghost" onClick={() => void logout()}>Sign out</button>
      </header>

      <section className="content">
        <div className="dashboard-hero">
          <div>
            <span className="badge badge-success">Secure clinical dashboard</span>
            <h1>Patients</h1>
          </div>
          <Link className="button-primary" to="/patients/new">
            <Plus size={18} /> Add Patient
          </Link>
        </div>

        <div className="feature-grid">
          <article className="icon-feature">
            <UserRound size={22} />
            <strong>{patients.length}</strong>
            <span>Active patients</span>
          </article>
          <article className="icon-feature">
            <FileText size={22} />
            <strong>0</strong>
            <span>Uploaded reports</span>
          </article>
          <article className="icon-feature">
            <ShieldCheck size={22} />
            <strong>Secure</strong>
            <span>Scoped records</span>
          </article>
          <article className="icon-feature">
            <ClipboardList size={22} />
            <strong>0</strong>
            <span>Draft plans</span>
          </article>
        </div>

        <div className="data-panel">
          <div className="panel-header">
            <div>
              <h2>Patient roster</h2>
              <span>{loading ? 'Loading records…' : `${patients.length} total`}</span>
            </div>
          </div>

          {error && <p className="error">{error}</p>}

          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td>{patient.patient_code}</td>
                  <td>{patient.first_name} {patient.last_name}</td>
                  <td>{new Date(patient.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {!loading && !error && patients.length === 0 && (
                <tr><td colSpan={3}>No patients yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
