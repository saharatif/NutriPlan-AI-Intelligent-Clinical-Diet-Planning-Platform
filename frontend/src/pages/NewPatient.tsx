import { Link, useNavigate } from 'react-router-dom';
import PatientStepForm from '../components/PatientStepForm';
import { api } from '../lib/api';
import { usePatientStore } from '../store/usePatientStore';
import type { PatientPayload } from '../store/usePatientStore';

export default function NewPatient() {
  const navigate   = useNavigate();
  const createPatient = usePatientStore((state) => state.createPatient);

  async function handleSubmit(payload: PatientPayload, files: File[]) {
    // 1. Create patient record
    const patient = await createPatient(payload) as { id: string };
    const patientId = patient.id;

    // 2. Upload PDFs and trigger OCR — errors here don't block navigation
    if (files.length > 0) {
      Promise.all(files.map(async (file) => {
        try {
          const form = new FormData();
          form.append('file', file);
          const docResponse = await api.post<{ id: string }>(
            `/patients/${patientId}/documents`,
            form
          );
          await api.post(`/patients/${patientId}/documents/${docResponse.data.id}/process`);
        } catch {
          // OCR runs in background — upload failure is non-fatal
        }
      })).catch(() => undefined);
    }

    navigate(`/patients/${patientId}`);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <strong>NutriPlan AI</strong>
          <span>New patient intake</span>
        </div>
        <Link className="button-ghost" to="/">← Back</Link>
      </header>

      <section className="content narrow">
        <div className="page-title">
          <h1>New Patient</h1>
          <p style={{ color: 'var(--slate)', fontSize: 14 }}>
            Complete all steps. PDFs are processed immediately — Mistral OCR extracts blood markers and all content is embedded into the vector database.
          </p>
        </div>
        <PatientStepForm onSubmit={handleSubmit} />
      </section>
    </main>
  );
}
