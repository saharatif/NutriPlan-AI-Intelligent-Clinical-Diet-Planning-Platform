import { ClipboardList, FileText, Plus, ShieldCheck, UserRound } from 'lucide-react';
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { usePatientStore } from '../store/usePatientStore';

export default function Dashboard() {
  const { patients, fetchPatients, loading, error } = usePatientStore();

  useEffect(() => { void fetchPatients(); }, [fetchPatients]);

  return (
    <Layout>
      <div className="page-header">
        <div>
          <h1>Patients</h1>
          <p style={{ color: 'var(--slate)', fontSize: 14, marginTop: 4 }}>
            {loading ? 'Loading…' : `${patients.length} patient${patients.length !== 1 ? 's' : ''} on record`}
          </p>
        </div>
        <Link className="button-primary" to="/patients/new"><Plus size={16} /> Add Patient</Link>
      </div>

      <div className="content">
        <div className="feature-grid">
          <article className="icon-feature">
            <UserRound size={20} />
            <strong>{patients.length}</strong>
            <span>Active patients</span>
          </article>
          <article className="icon-feature">
            <FileText size={20} />
            <strong>0</strong>
            <span>Uploaded reports</span>
          </article>
          <article className="icon-feature">
            <ShieldCheck size={20} />
            <strong>RLS</strong>
            <span>Data isolated</span>
          </article>
          <article className="icon-feature">
            <ClipboardList size={20} />
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
                <th>Patient</th>
                <th>Added</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td><span className="profile-chip">{patient.patient_code}</span></td>
                  <td style={{ fontWeight: 500 }}>{patient.first_name} {patient.last_name}</td>
                  <td style={{ color: 'var(--slate)' }}>{new Date(patient.created_at).toLocaleDateString()}</td>
                  <td><Link className="table-link" to={`/patients/${patient.id}`}>View →</Link></td>
                </tr>
              ))}
              {!loading && !error && patients.length === 0 && (
                <tr><td colSpan={4} style={{ color: 'var(--slate)', textAlign: 'center', padding: '32px' }}>
                  No patients yet — <Link className="table-link" to="/patients/new">add your first patient</Link>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
