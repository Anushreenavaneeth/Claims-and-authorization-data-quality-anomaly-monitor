import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { getDashboardSummary, getIntegratedAnomalies } from "../services/integratedApi";
import { formatNumber } from "../lib/utils";
import { AlertCircle, Clock, CheckCircle } from "lucide-react";
import type { IntegratedRecord } from "../types/integrated";

export function SLAPage() {
  const [breached, setBreached] = useState<IntegratedRecord[]>([]);
  const [atRisk,   setAtRisk]   = useState<IntegratedRecord[]>([]);
  const [normal,   setNormal]   = useState<IntegratedRecord[]>([]);
  const [totalSLA, setTotalSLA] = useState(0);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getIntegratedAnomalies({ sla_status: "BREACHED",  page_size: 100, is_anomaly: true }),
      getIntegratedAnomalies({ sla_status: "AT_RISK",   page_size: 100, is_anomaly: true }),
      getIntegratedAnomalies({ sla_status: "NORMAL",    page_size: 50,  is_anomaly: false }),
      getDashboardSummary(),
    ]).then(([b, r, n, s]) => {
      setBreached(b.items);
      setAtRisk(r.items);
      setNormal(n.items);
      setTotalSLA(s.sla_breaches + s.sla_at_risk);
    }).finally(() => setLoading(false));
  }, []);

  const columns: Column<IntegratedRecord>[] = [
    { key: "record_id", label: "Record ID",   sortable: true, className: "font-mono text-xs" },
    { key: "dataset",   label: "Dataset",     sortable: true, render: r => <span className="capitalize">{r.dataset}</span> },
    { key: "sla",       label: "Risk Score",  sortable: false, render: r => r.sla.risk_score.toFixed(1) },
    { key: "sla_s",     label: "SLA Status",  sortable: false, render: r => <StatusBadge status={r.sla.status} /> },
    { key: "sla_p",     label: "Priority",    sortable: false, render: r => <StatusBadge status={r.sla.priority} type="priority" /> },
    { key: "resp",      label: "Response Time", sortable: false, render: r => r.sla.response_time },
    { key: "esc",       label: "Escalation",  sortable: false,
      render: r => <span className={r.sla.escalation_required ? "text-red-600 font-medium" : "text-green-600"}>
        {r.sla.escalation_required ? "Required" : "No"}
      </span> },
    { key: "sev",       label: "Severity",    sortable: false,
      render: r => <StatusBadge status={r.anomaly.severity} type="severity" /> },
  ];

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading SLA data…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">SLA &amp; Priority Dashboard</h1>
        <p className="text-muted-foreground mt-1">Monitor SLA compliance and prioritize resolution efforts</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Total SLA Issues</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{formatNumber(totalSLA)}</div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">SLA Breached</CardTitle></CardHeader>
          <CardContent><div className="flex items-center gap-2"><AlertCircle className="h-5 w-5 text-red-600" /><div className="text-2xl font-bold text-red-600">{breached.length}</div></div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">At Risk</CardTitle></CardHeader>
          <CardContent><div className="flex items-center gap-2"><Clock className="h-5 w-5 text-orange-600" /><div className="text-2xl font-bold text-orange-600">{atRisk.length}</div></div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Normal</CardTitle></CardHeader>
          <CardContent><div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-600" /><div className="text-2xl font-bold text-green-600">{normal.length}</div></div></CardContent></Card>
      </div>

      {/* Risk lanes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { title: "Breached", items: breached, color: "text-red-600", border: "border-red-200", bg: "bg-red-50", icon: AlertCircle },
          { title: "At Risk",  items: atRisk,   color: "text-orange-600", border: "border-orange-200", bg: "bg-orange-50", icon: Clock },
          { title: "Normal",   items: normal,   color: "text-green-600", border: "border-green-200", bg: "bg-green-50", icon: CheckCircle },
        ].map(({ title, items, color, border, bg, icon: Icon }) => (
          <Card key={title}>
            <CardHeader>
              <CardTitle className={`${color} flex items-center gap-2`}>
                <Icon className="h-5 w-5" />{title} ({items.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {items.length === 0 ? (
                <p className="text-sm text-muted-foreground">No items</p>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {items.slice(0, 10).map(r => (
                    <div key={r.record_id} className={`p-3 border ${border} rounded-lg ${bg}`}>
                      <div className="font-medium text-xs font-mono truncate">{r.record_id}</div>
                      <div className="text-xs text-muted-foreground mt-1 capitalize">
                        {r.dataset} · Risk {r.sla.risk_score.toFixed(1)} · {r.sla.priority}
                      </div>
                    </div>
                  ))}
                  {items.length > 10 && (
                    <p className="text-xs text-muted-foreground text-center">+{items.length - 10} more</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Full table */}
      <Card>
        <CardHeader><CardTitle>All Breached &amp; At-Risk Records</CardTitle></CardHeader>
        <CardContent>
          <DataTable data={[...breached, ...atRisk]} columns={columns} />
        </CardContent>
      </Card>
    </div>
  );
}
