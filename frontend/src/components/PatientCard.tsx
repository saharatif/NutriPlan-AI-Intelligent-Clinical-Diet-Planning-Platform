import { Link } from 'react-router-dom';
import type { PatientListItem } from '../store/usePatientStore';

export default function PatientCard({ patient }: { patient: PatientListItem }) {
  return (
    <Link className="patient-card" to={`/patients/${patient.id}`}>
      <strong>{patient.first_name} {patient.last_name}</strong>
      <span>{patient.patient_code}</span>
      <small>Created {new Date(patient.created_at).toLocaleDateString()}</small>
    </Link>
  );
}
