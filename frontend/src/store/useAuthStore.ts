import type { Session } from '@supabase/supabase-js';
import { create } from 'zustand';
import { api } from '../lib/api';
import { supabase } from '../lib/supabase';

export type DoctorProfile = {
  id: string;
  email: string;
  name: string;
  clinic?: string | null;
};

type AuthState = {
  session: Session | null;
  doctor: DoctorProfile | null;
  loading: boolean;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string, clinic: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchDoctor: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  doctor: null,
  loading: true,
  initialize: async () => {
    try {
      const { data } = await supabase.auth.getSession();
      set({ session: data.session });
      if (data.session) await get().fetchDoctor();
    } catch {
      // Supabase not yet configured — app renders but auth is non-functional
    } finally {
      set({ loading: false });
    }
  },
  login: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    set({ session: data.session });
    const response = await api.post<DoctorProfile>('/auth/login');
    set({ doctor: response.data });
  },
  signUp: async (email, password, name, clinic) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name, clinic } }
    });
    if (error) throw error;
    set({ session: data.session });
    if (data.session) {
      const response = await api.post<DoctorProfile>('/auth/login');
      set({ doctor: response.data });
    }
  },
  logout: async () => {
    await api.post('/auth/logout').catch(() => undefined);
    await supabase.auth.signOut();
    set({ session: null, doctor: null });
  },
  fetchDoctor: async () => {
    const response = await api.get<DoctorProfile>('/auth/me');
    set({ doctor: response.data });
  }
}));
