import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import WorkerDashboard from './pages/WorkerDashboard';
import WorkerManagement from './pages/WorkerManagement';
import AnomaliesPage from './pages/AnomaliesPage';
import AnomalyDetailPage from './pages/AnomalyDetailPage';
import DataSources from './pages/DataSources';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Admin routes */}
          <Route path="/admin/dashboard" element={
            <ProtectedRoute requiredRole="admin"><AdminDashboard /></ProtectedRoute>
          } />

          <Route path="/admin/workers" element={
            <ProtectedRoute requiredRole="admin"><WorkerManagement /></ProtectedRoute>
          } />

          <Route path="/admin/anomalies/:recordId" element={
            <ProtectedRoute requiredRole="admin"><AnomalyDetailPage /></ProtectedRoute>
          } />

          <Route path="/admin/anomalies" element={
            <ProtectedRoute requiredRole="admin"><AnomaliesPage /></ProtectedRoute>
          } />

          <Route path="/admin/data-sources" element={
            <ProtectedRoute requiredRole="admin"><DataSources /></ProtectedRoute>
          } />

          {/* Worker routes */}
          <Route path="/worker/dashboard" element={
            <ProtectedRoute requiredRole="worker"><WorkerDashboard /></ProtectedRoute>
          } />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
