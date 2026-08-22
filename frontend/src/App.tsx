import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import { Layout } from "./components/Layout";

// Pages
import Login             from "./pages/Login";
import { Overview }      from "./pages/Overview";
import { AnomaliesNew }  from "./pages/AnomaliesNew";
import AnomalyDetailPage from "./pages/AnomalyDetailPage";
import { SLAPage }             from "./pages/SLAPage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { MonitoringPage }      from "./pages/MonitoringPage";
import { ReviewPage }          from "./pages/ReviewPage";
import { ResolutionsPage }     from "./pages/ResolutionsPage";
import WorkerManagement  from "./pages/WorkerManagement";
import DataSources       from "./pages/DataSources";
import WorkerDashboard   from "./pages/WorkerDashboard";

// Lightweight placeholder for pages not yet wired
function Placeholder({ title }: { title: string }) {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="text-muted-foreground">Coming soon — this section is under development.</p>
    </div>
  );
}

function AdminLayout() {
  return (
    <ProtectedRoute requiredRole="admin">
      <Layout />
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<Login />} />

          {/* Admin — all routes share the sidebar layout */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index                 element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard"      element={<Overview />} />
            <Route path="anomalies"      element={<AnomaliesNew />} />
            <Route path="anomalies/:recordId" element={<AnomalyDetailPage />} />
            <Route path="sla"            element={<SLAPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="monitoring"     element={<MonitoringPage />} />
            <Route path="workers"        element={<WorkerManagement />} />
            <Route path="data-sources"   element={<DataSources />} />
            <Route path="quality"        element={<Placeholder title="Data Quality Checks" />} />
            <Route path="review"         element={<ReviewPage />} />
            <Route path="resolutions"    element={<ResolutionsPage />} />
            <Route path="feedback"       element={<Placeholder title="Feedback Loop" />} />
          </Route>

          {/* Worker — uses same Layout but with worker nav */}
          <Route path="/worker" element={
            <ProtectedRoute requiredRole="worker"><Layout /></ProtectedRoute>
          }>
            <Route index          element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<WorkerDashboard />} />
          </Route>

          {/* Default */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
