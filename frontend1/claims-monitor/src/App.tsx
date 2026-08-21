import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { Overview } from "./pages/Overview";
import { DataSources } from "./pages/DataSources";
import { QualityChecks } from "./pages/QualityChecks";
import { Anomalies } from "./pages/Anomalies";
import { MLScoring } from "./pages/MLScoring";
import { SLA } from "./pages/SLA";
import { Recommendations } from "./pages/Recommendations";
import { Review } from "./pages/Review";
import { Resolutions } from "./pages/Resolutions";
import { Monitoring } from "./pages/Monitoring";
import { FeedbackPage } from "./pages/Feedback";
import { WorkersPage } from "./pages/Workers";
import { AuditTrailPage } from "./pages/AuditTrail";
import { NotificationSettingsPage } from "./pages/NotificationSettings";
import Login from "./pages/Login";
import { SetPassword } from "./pages/SetPassword";
import { NotFound } from "./pages/NotFound";
import { Loader2 } from "lucide-react";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#010408] text-white">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/set-password" element={<SetPassword />} />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Overview />} />
            <Route path="data-sources" element={<DataSources />} />
            <Route path="quality-checks" element={<QualityChecks />} />
            <Route path="anomalies" element={<Anomalies />} />
            <Route path="ml-engine" element={<MLScoring />} />
            <Route path="sla" element={<SLA />} />
            <Route path="recommendations" element={<Recommendations />} />
            <Route path="review" element={<Review />} />
            <Route path="resolutions" element={<Resolutions />} />
            <Route path="audit-trail" element={<AuditTrailPage />} />
            <Route path="workers" element={<WorkersPage />} />
            <Route path="notifications" element={<NotificationSettingsPage />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
