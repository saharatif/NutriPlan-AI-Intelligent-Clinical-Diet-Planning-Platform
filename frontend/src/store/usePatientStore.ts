import { create } from 'zustand';
import { api } from '../lib/api';

export type PatientListItem = {
  id: string;
  patient_code: string;
  first_name: string;
  last_name: string;
  created_at: string;
};

export type DietaryPreference = 'vegan' | 'vegetarian' | 'pescatarian' | 'flexitarian';

export type PatientPayload = {
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  sex?: 'male' | 'female' | 'other';
  height_cm?: number;
  weight_kg?: number;
  notes?: string;
  ethnicity?: string;
  dietary_preference?: DietaryPreference;
  conditions?: Array<{ name: string; notes?: string }>;
  medications?: Array<{ name: string; dosage?: string; frequency?: string }>;
  allergens?: Array<{ name: string; severity?: string }>;
  family_history?: Array<{ condition: string; relationship?: string }>;
  favourite_foods?: Array<{ name: string; preference_level?: number }>;
};

type PatientState = {
  patients: PatientListItem[];
  selectedPatient: PatientListItem | null;
  loading: boolean;
  error: string | null;
  fetchPatients: () => Promise<void>;
  createPatient: (payload: PatientPayload) => Promise<unknown>;
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
    const response = await api.post('/patients', payload);
    await get().fetchPatients();
    return response.data;
  },
}));
