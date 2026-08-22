import { useEffect, useState, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Input } from "../components/ui/Input";
import { getIntegratedAnomalies } from "../services/integratedApi";
import { formatNumber, getSeverityColor } from "../lib/utils";
import { AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";
import type { IntegratedRecord } from "../types/integrated";

const PAGE_SIZE = 50;

function SeverityBadge({ severity }: { severity: string }) {
  const cls = getSeverityColor(severity);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {severity}
    </span>
  );
}

export function AnomaliesNew() {
  const navigate       = useNavigate();
  const [searchParams] = useSearchParams();

  const [items,    setItems]    = useState<IntegratedRecord[]>([]);
  const [total,    setTotal]    = useState(0);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);

  const [dataset,   setDataset]   = useState(searchParams.get("dataset")    ?? "");
  const [severity,  setSeverity]  = useState(searchParams.get("severity")   ?? "");
  const [slaStatus, setSlaStatus] = useState(searchParams.get("sla_status") ?? "");
  const [search,    setSearch]    = useState("");
  const [page,      setPage]      = useState(1);

  const fetch = useCallback(() => {
    setLoading(true);
    const p: Record<string, unknown> = { page, page_size: PAGE_SIZE };
    if (dataset)   p.dataset    = dataset;
    if (severity)  p.severity   = severity;
    if (slaStatus) p.sla_status = slaStatus;
    if (search)    p.search     = search;
    p.is_anomaly = true;
    getIntegratedAnomalies(p as any)
      .then(r => { setItems(r.items); setTotal(r.total); })
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? "Failed"))
      .finally(() => setLoading(false));
  }, [dataset, severity, slaStatus, search, page]);

  useEffect(() => { fetch(); }, [fetch]);

  const columns: Column<IntegratedRecord>[] = [
    { key: "record_id",       label: "Record ID",     sortable: true, className: "font-mono text-xs" },
    { key: "dataset",         label: "Dataset",       sortable: true,
      render: r => <Badge variant="info" className="capitalize">{r.dataset}</Badge> },
    { key: "anomaly",         label: "Anomaly Score", sortable: false,
      render: r => r.anomaly.anomaly_score.toFixed(3) },
    { key: "quality",         label: "Quality",       sortable: false,
      render: r => `${r.quality.quality_score.toFixed(0)}%` },
    { key: "sla",             label: "Risk Score",    sortable: false,
      render: r => r.sla.risk_score.toFixed(1) },
    { key: "anomaly_sev",     label: "Severity",      sortable: false,
      render: r => <SeverityBadge severity={r.anomaly.severity} /> },
    { key: "rules",           label: "Root Cause",    sortable: false,
      render: r => <span className="text-xs truncate max-w-[160px] block">
        {r.rules.rule_names[0]?.replace(/_/g, " ") || (r.bayesian.is_anomaly ? "Bayesian flag" : "—")}
      </span> },
    { key: "sla_status",      label: "SLA Status",    sortable: false,
      render: r => <StatusBadge status={r.sla.status} /> },
    { key: "sla_priority",    label: "Priority",      sortable: false,
      render: r => <StatusBadge status={r.sla.priority} type="priority" /> },
  ];

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Anomaly Detection &amp; Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Review and analyse detected data anomalies across all datasets
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Total Anomalies</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{formatNumber(total)}</div></CardContent></Card>
        {[["Claims","claims"],["Authorization","authorization"],["Pharmacy","pharmacy"]].map(([label, val]) => (
          <Card key={val}>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600 cursor-pointer"
                   onClick={() => { setDataset(val); setPage(1); }}>
                {dataset === val ? items.length : "Filter →"}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <CardHeader><CardTitle>Detected Anomalies</CardTitle></CardHeader>
        <CardContent>
          <div className="mb-4 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">Dataset:</span>
              {["", "claims", "authorization", "pharmacy"].map(v => (
                <button key={v} onClick={() => { setDataset(v); setPage(1); }}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${dataset === v ? "bg-primary text-primary-foreground" : "bg-secondary hover:bg-secondary/80"}`}>
                  {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">Severity:</span>
              {["", "CRITICAL","HIGH","MEDIUM","LOW"].map(v => (
                <button key={v} onClick={() => { setSeverity(v); setPage(1); }}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${severity === v ? "bg-primary text-primary-foreground" : "bg-secondary hover:bg-secondary/80"}`}>
                  {v === "" ? "All" : v}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium">SLA:</span>
              {["","BREACHED","AT_RISK","ELEVATED","NORMAL"].map(v => (
                <button key={v} onClick={() => { setSlaStatus(v); setPage(1); }}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${slaStatus === v ? "bg-primary text-primary-foreground" : "bg-secondary hover:bg-secondary/80"}`}>
                  {v === "" ? "All" : v}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <Input
                placeholder="Search record ID…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="max-w-xs"
              />
            </div>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 text-red-600 text-sm">
              <AlertTriangle className="h-4 w-4" />{error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-12 text-muted-foreground">Loading…</div>
          ) : (
            <DataTable
              data={items}
              columns={columns}
              onRowClick={row => navigate(`/admin/anomalies/${encodeURIComponent(row.record_id)}`)}
            />
          )}

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                {((page-1)*PAGE_SIZE)+1}–{Math.min(page*PAGE_SIZE, total)} of {formatNumber(total)}
              </p>
              <div className="flex items-center gap-2">
                <button disabled={page<=1} onClick={() => setPage(p=>p-1)}
                  className="p-1.5 rounded border disabled:opacity-30 hover:bg-accent">
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm">{page} / {totalPages}</span>
                <button disabled={page>=totalPages} onClick={() => setPage(p=>p+1)}
                  className="p-1.5 rounded border disabled:opacity-30 hover:bg-accent">
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
