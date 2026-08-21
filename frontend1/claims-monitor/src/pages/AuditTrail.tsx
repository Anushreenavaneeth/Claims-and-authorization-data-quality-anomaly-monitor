import { History } from "lucide-react";

export function AuditTrailPage() {
  const auditLogs = [
    { id: "LOG-1001", action: "DATASET_UPLOAD", user: "Admin User", details: "Uploaded mock_authorization.csv (50 records)", timestamp: "2026-08-21 17:45:12" },
    { id: "LOG-1002", action: "ANOMALY_FLAGGED", user: "ML Engine", details: "Flagged SLA Processing Spike on AUTH_902", timestamp: "2026-08-21 17:45:15" },
    { id: "LOG-1003", action: "WORKER_CREATED", user: "Admin User", details: "Created worker account Middle-man (gandhi1@gmail.com)", timestamp: "2026-08-21 16:30:00" },
    { id: "LOG-1004", action: "USER_LOGIN", user: "Worker User", details: "Successful authentication from 127.0.0.1", timestamp: "2026-08-21 15:12:40" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-foreground">Audit Trail & Activity Log</h1>
        <p className="text-xs font-mono text-muted-foreground mt-1">
          Immutable log of operator actions, system events, and anomaly remediation records.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <h3 className="font-bold text-sm flex items-center gap-2">
            <History className="w-4 h-4 text-primary" /> System Activity Log
          </h3>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              {["Log ID", "Action", "User / System", "Details", "Timestamp"].map((h) => (
                <th key={h} className="px-5 py-3 text-left text-[10px] font-mono tracking-widest text-muted-foreground uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {auditLogs.map((log) => (
              <tr key={log.id} className="hover:bg-accent/40 transition-colors font-mono text-xs">
                <td className="px-5 py-3.5 text-primary font-bold">{log.id}</td>
                <td className="px-5 py-3.5 font-bold text-foreground">{log.action}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{log.user}</td>
                <td className="px-5 py-3.5 text-foreground">{log.details}</td>
                <td className="px-5 py-3.5 text-muted-foreground">{log.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default AuditTrailPage;
