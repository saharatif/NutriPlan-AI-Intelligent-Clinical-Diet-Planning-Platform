import { createClient } from '@supabase/supabase-js';

const supabaseUrl     = import.meta.env.VITE_SUPABASE_URL     as string | undefined;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[NutriPlan] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set. ' +
    'Fill in both VITE_ vars in your root .env file — auth will not work until then.'
  );
}

// Use placeholder values so the module loads and the UI renders even without credentials.
// Auth calls will fail at runtime, not at startup.
export const supabase = createClient(
  supabaseUrl     || 'http://localhost',
  supabaseAnonKey || 'placeholder-key',
);
