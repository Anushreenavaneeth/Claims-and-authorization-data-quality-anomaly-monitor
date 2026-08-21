/**
 * AnomaliesPlaceholder
 * ---------------------
 * Temporary page holding the /admin/anomalies route.
 * Full-Stack 2 will replace this with:
 *   features/anomalies/AnomaliesPage.tsx
 *
 * Backend contract:
 *   GET  /anomalies              → AnomalyListResponse
 *   GET  /anomalies/{id}         → AnomalyResponse
 *   PATCH /anomalies/{id}/status → AnomalyResponse
 *   POST  /anomalies/{id}/rerun  → { message, anomaly_id }
 *   WS    /anomalies/ws          → NEW_ANOMALY | STATUS_CHANGED events
 */
import DashboardShell from '../components/DashboardShell';
import { AlertTriangle } from 'lucide-react';

export default function AnomaliesPlaceholder() {
  return (
    <DashboardShell>
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)' }}
        >
          <AlertTriangle className="w-6 h-6 text-red-400" />
        </div>
        <p className="text-[10px] font-mono tracking-widest text-slate-600 uppercase mb-2">Admin · Anomalies</p>
        <h2 className="font-display text-xl font-bold text-white mb-2">Anomaly Dashboard</h2>
        <p className="text-sm font-mono text-slate-500 max-w-sm leading-relaxed">
          Full-Stack 2 is building this module.<br />
          Backend APIs are live at <code className="text-blue-400">/anomalies</code>
          {' '}and <code className="text-blue-400">/anomalies/ws</code>.
        </p>
      </div>
    </DashboardShell>
  );
}
