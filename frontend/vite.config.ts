import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

// Load VITE_ vars from the repo root .env so developers only maintain one env file
export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), 'VITE_');

  return {
    plugins: [react()],
    define: {
      'import.meta.env.VITE_SUPABASE_URL':     JSON.stringify(rootEnv.VITE_SUPABASE_URL     ?? ''),
      'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify(rootEnv.VITE_SUPABASE_ANON_KEY ?? ''),
    },
    server: {
      port: 5173,
      proxy: {
        '/api':    'http://localhost:8000',
        '/health': 'http://localhost:8000',
      },
    },
  };
});
