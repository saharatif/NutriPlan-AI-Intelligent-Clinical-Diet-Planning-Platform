import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DietPlan from './pages/DietPlan';
import DietPlanReview from './pages/DietPlanReview';
import GenerateDietPlan from './pages/GenerateDietPlan';
import Login from './pages/Login';
import NewPatient from './pages/NewPatient';
import PatientProfile from './pages/PatientProfile';
import { useAuthStore } from './store/useAuthStore';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { session, loading } = useAuthStore();
  const location = useLocation();
  if (loading) return <main className="screen">Loading...</main>;
  if (!session) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Layout>{children}</Layout>;
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
      <Route path="/patients/:patientId" element={<ProtectedRoute><PatientProfile /></ProtectedRoute>} />
      <Route path="/patients/:patientId/generate" element={<ProtectedRoute><GenerateDietPlan /></ProtectedRoute>} />
      <Route path="/diet-plans/:planId/review" element={<ProtectedRoute><DietPlanReview /></ProtectedRoute>} />
      <Route path="/diet-plans/:planId" element={<ProtectedRoute><DietPlan /></ProtectedRoute>} />
    </Routes>
  );
}
