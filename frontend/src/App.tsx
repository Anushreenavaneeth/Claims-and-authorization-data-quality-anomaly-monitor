import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import ProtectedRoute from './auth/ProtectedRoute';
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import WorkerDashboard from './pages/WorkerDashboard';
import WorkerManagement from './pages/WorkerManagement';
import AnomaliesPlaceholder from './pages/AnomaliesPlaceholder';
import DataSources from './pages/DataSources';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/admin/dashboard" element={
            <ProtectedRoute requiredRole="admin"><AdminDashboard /></ProtectedRoute>
          } />

          <Route path="/admin/workers" element={
            <ProtectedRoute requiredRole="admin"><WorkerManagement /></ProtectedRoute>
          } />

          {/* Full-Stack 2 will replace AnomaliesPlaceholder with their AnomaliesPage */}
          <Route path="/admin/anomalies" element={
            <ProtectedRoute requiredRole="admin"><AnomaliesPlaceholder /></ProtectedRoute>
          } />

          <Route path="/admin/data-sources" element={
            <ProtectedRoute requiredRole="admin"><DataSources /></ProtectedRoute>
          } />

          <Route path="/worker/dashboard" element={
            <ProtectedRoute requiredRole="worker"><WorkerDashboard /></ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
