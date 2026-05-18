import { RefreshCw, ScanText, Upload } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import AuditLogTable, { AuditLog } from '../components/AuditLogTable';
import MedicalProfileCard, { MedicalProfile } from '../components/MedicalProfileCard';
import OCRResultViewer, { BloodTestResult } from '../components/OCRResultViewer';
import { api } from '../lib/api';

type Document = {
  id: string;
  file_name: string;
  ocr_status: string;
  ocr_processed: boolean;
};

type Patient = {
  patient_code: string;
  first_name: string;
  last_name: string;
  allergens: Array<{ name: string; severity?: string | null }>;
  documents: Document[];
};

export default function PatientProfile() {
  const { patientId } = useParams();
  const [patient,  setPatient]  = useState<Patient | null>(null);
  const [markers,  setMarkers]  = useState<BloodTestResult[]>([]);
  const [profile,  setProfile]  = useState<MedicalProfile | null>(null);
  const [plans,    setPlans]    = useState<Array<{ id: string; status: string; plan_type: string }>>([]);
  const [logs,     setLogs]     = useState<AuditLog[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [processing, setProcessing] = useState<Record<string, boolean>>({});
  const [uploading,  setUploading]  = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function load() {
    if (!patientId) return;
    setLoading(true);
    try {
      const [patientRes, markerRes] = await Promise.all([
        api.get<Patient>(`/patients/${patientId}`),
        api.get<BloodTestResult[]>(`/patients/${patientId}/blood-tests`),
      ]);
      setPatient(patientRes.data);
      setMarkers(markerRes.data);
      const [planRes, logRes] = await Promise.all([
        api.get<Array<{ id: string; status: string; plan_type: string }>>(`/patients/${patientId}/diet-plans`).catch(() => ({ data: [] })),
        api.get<AuditLog[]>(`/patients/${patientId}/audit-logs`).catch(() => ({ data: [] })),
      ]);
      setPlans(planRes.data);
      setLogs(logRes.data);
      try {
        const profileRes = await api.get<MedicalProfile>(`/patients/${patientId}/medical-profile`);
        setProfile(profileRes.data);
      } catch { setProfile(null); }
    } finally {
      setLoading(false);
    }
  }

  async function rebuildProfile() {
    if (!patientId) return;
    const res = await api.post<MedicalProfile>(`/patients/${patientId}/medical-profile/build`);
    setProfile(res.data);
  }

  async function processDocument(docId: string) {
    if (!patientId) return;
    setProcessing((prev) => ({ ...prev, [docId]: true }));
    try {
      await api.post(`/patients/${patientId}/documents/${docId}/process`);
      // Poll until done
      const poll = setInterval(async () => {
        const res = await api.get<Document[]>(`/patients/${patientId}/documents`)
          .then((r) => r.data.find((d) => d.id === docId));
        if (res?.ocr_processed || res?.ocr_status === 'failed') {
          clearInterval(poll);
          setProcessing((prev) => ({ ...prev, [docId]: false }));
          void load();
        }
      }, 2500);
    } catch {
      setProcessing((prev) => ({ ...prev, [docId]: false }));
    }
  }

  async function uploadFiles(files: FileList | null) {
    if (!files || !patientId) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        if (file.type !== 'application/pdf') continue;
        const form = new FormData();
        form.append('file', file);
        await api.post(`/patients/${patientId}/documents`, form);
      }
      void load();
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => { void load(); }, [patientId]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <strong>NutriPlan AI</strong>
          <span>{patient?.patient_code ?? 'Patient profile'}</span>
        </div>
        <Link className="button-ghost" to="/">← Back</Link>
      </header>

      <section className="content">
        <div className="dashboard-hero">
          <div>
            <h1>{patient ? `${patient.first_name} ${patient.last_name}` : 'Patient Profile'}</h1>
            <p style={{ color: 'var(--slate)', fontSize: 14, marginTop: 4 }}>
              {loading ? 'Loading…' : `${patient?.patient_code} · ${markers.length} blood markers extracted`}
            </p>
          </div>
          <button className="button-primary" onClick={() => void rebuildProfile()}>
            <RefreshCw size={15} /> Rebuild Profile
          </button>
        </div>

        <div className="profile-layout">
          <MedicalProfileCard profile={profile} />

          {/* Documents panel */}
          <section className="checkout-summary">
            <div className="panel-header">
              <div><h2>Documents</h2><span>Blood test PDFs</span></div>
              <button
                className="button-ghost"
                style={{ minHeight: 34, padding: '0 12px', fontSize: 13 }}
                disabled={uploading}
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={14} /> {uploading ? 'Uploading…' : 'Upload PDF'}
              </button>
              <input
                ref={fileRef}
                type="file"
                accept="application/pdf"
                multiple
                style={{ display: 'none' }}
                onChange={(e) => void uploadFiles(e.target.files)}
              />
            </div>

            <div className="document-list">
              {patient?.documents.map((doc) => (
                <div className="document-row" key={doc.id} style={{ gridTemplateColumns: '1fr auto auto' }}>
                  <span style={{ fontSize: 13 }}>{doc.file_name}</span>
                  <span className={doc.ocr_processed ? 'badge badge-success' : 'badge badge-warning'}>
                    {doc.ocr_status}
                  </span>
                  {!doc.ocr_processed && (
                    <button
                      className="button-primary"
                      style={{ minHeight: 30, padding: '0 12px', fontSize: 12 }}
                      disabled={processing[doc.id]}
                      onClick={() => void processDocument(doc.id)}
                    >
                      <ScanText size={13} />
                      {processing[doc.id] ? 'Processing…' : 'Process'}
                    </button>
                  )}
                </div>
              ))}
              {!patient?.documents.length && (
                <span className="empty-copy">No documents yet — upload a blood test PDF above.</span>
              )}
            </div>
          </section>
        </div>

        {/* Plans + Audit */}
        <div className="profile-layout">
          <section className="checkout-summary">
            <div className="panel-header"><div><h2>Saved plans</h2><span>{plans.length} plans</span></div></div>
            <div className="document-list">
              {plans.map((plan) => (
                <Link
                  key={plan.id}
                  className="document-row table-link"
                  to={`/diet-plans/${plan.id}${plan.status === 'approved' ? '' : '/review'}`}
                >
                  <span>{plan.plan_type}</span>
                  <span className={`badge ${plan.status === 'approved' ? 'badge-success' : 'badge-warning'}`}>
                    {plan.status}
                  </span>
                </Link>
              ))}
              {plans.length === 0 && (
                <Link className="button-primary" to={`/patients/${patientId}/generate`}>
                  Generate Plan
                </Link>
              )}
            </div>
          </section>
          <AuditLogTable logs={logs} />
        </div>

        <OCRResultViewer results={markers} />
      </section>
    </main>
  );
}
