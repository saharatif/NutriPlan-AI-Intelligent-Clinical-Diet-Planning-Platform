import { create } from 'zustand';
import { api } from '../lib/api';

export type PatientListItem = {
  id: string;
  patient_code: string;
  first_name: string;
  last_name: string;
  created_at: string;
};

export type PatientPayload = {
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  sex?: 'male' | 'female' | 'other';
  height_cm?: number;
  weight_kg?: number;
  conditions?: Array<{ name: string; notes?: string }>;
};

type PatientState = {
  patients: PatientListItem[];
  selectedPatient: PatientListItem | null;
  loading: boolean;
  error: string | null;
  fetchPatients: () => Promise<void>;
  createPatient: (payload: PatientPayload) => Promise<void>;
};

export const usePatientStore = create<PatientState>((set, get) => ({
  patients: [],
  selectedPatient: null,
  loading: false,
  error: null,
  fetchPatients: async () => {
    set({ loading: true, error: null });
    try {
      const response = await api.get<PatientListItem[]>('/patients');
      set({ patients: response.data });
    } catch {
      set({ error: 'Failed to load patients. Please refresh the page.' });
    } finally {
      set({ loading: false });
    }
  },
  createPatient: async (payload) => {
    await api.post('/patients', payload);
    await get().fetchPatients();
  },
}));
