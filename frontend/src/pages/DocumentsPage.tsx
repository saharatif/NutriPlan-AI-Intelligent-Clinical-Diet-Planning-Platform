import { FileText } from 'lucide-react';

export default function DocumentsPage() {
  return (
    <div className="content">
      <div className="page-header">
        <div>
          <h1>Documents</h1>
          <p style={{ color: 'var(--slate)', fontSize: 14, marginTop: 4 }}>
            Patient blood reports and clinical documents
          </p>
        </div>
      </div>

      <div className="coming-soon-panel">
        <FileText size={40} strokeWidth={1.5} color="var(--steel)" />
        <h2>Coming soon</h2>
        <p>
          The Documents module will let you upload and manage patient blood reports and clinical files —
          which are then used by the AI to generate personalised, clinically-informed diet plans.
        </p>
        <ul className="coming-soon-list">
          <li>Upload PDF blood test reports per patient</li>
          <li>AI extracts key markers (HbA1c, cholesterol, iron, etc.)</li>
          <li>Documents linked directly to plan generation context</li>
          <li>Secure storage with clinic-level access control</li>
        </ul>
      </div>
    </div>
  );
}
