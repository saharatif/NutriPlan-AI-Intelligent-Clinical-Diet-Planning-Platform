import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import NewPatient from './pages/NewPatient';
import { useAuthStore } from './store/useAuthStore';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { session, loading } = useAuthStore();
  const location = useLocation();
  if (loading) return <main className="screen">Loading...</main>;
  if (!session) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

export default function App() {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/patients/new" element={<ProtectedRoute><NewPatient /></ProtectedRoute>} />
    </Routes>
  );
}
