import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Overview } from "./pages/Overview";
import { DataSources } from "./pages/DataSources";
import { QualityChecks } from "./pages/QualityChecks";
import { Anomalies } from "./pages/Anomalies";
import { SLA } from "./pages/SLA";
import { Recommendations } from "./pages/Recommendations";
import { Review } from "./pages/Review";
import { Resolutions } from "./pages/Resolutions";
import { Monitoring } from "./pages/Monitoring";
import { FeedbackPage } from "./pages/Feedback";
import { NotFound } from "./pages/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="data-sources" element={<DataSources />} />
          <Route path="quality-checks" element={<QualityChecks />} />
          <Route path="anomalies" element={<Anomalies />} />
          <Route path="sla" element={<SLA />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="review" element={<Review />} />
          <Route path="resolutions" element={<Resolutions />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="feedback" element={<FeedbackPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
