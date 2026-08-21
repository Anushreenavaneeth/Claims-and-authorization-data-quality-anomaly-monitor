import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Modal } from "../components/ui/Modal";
import { Badge } from "../components/ui/Badge";
import { getAnomalies, updateAnomalyStatus } from "../services/api";
import { formatNumber, formatDate, getSeverityColor } from "../lib/utils";
import { AlertTriangle, DollarSign, Activity, Search, RefreshCw, Radio, CheckCircle, ShieldAlert, Cpu } from "lucide-react";
import type { Anomaly } from "../types";

export function Anomalies() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [severityFilter, setSeverityFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isLiveSync, setIsLiveSync] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastActionMsg, setLastActionMsg] = useState<string | null>(null);

  useEffect(() => {
    loadAnomalies();
  }, []);

  // Realtime Auto-Polling Interval (every 3 seconds)
  useEffect(() => {
    if (!isLiveSync) return;

    const interval = setInterval(() => {
      loadAnomalies(true);
    }, 3000);

    return () => clearInterval(interval);
  }, [isLiveSync]);

  const loadAnomalies = async (silent = false) => {
    if (!silent) setIsRefreshing(true);
    try {
      const data = await getAnomalies();
      setAnomalies(data);
    } catch {
      // Keep existing state on transient network error
    } finally {
      if (!silent) setIsRefreshing(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'IGNORED') => {
    await updateAnomalyStatus(id, newStatus);
    setSelectedAnomaly(null);

    const statusLabel = newStatus === "RESOLVED" ? "Resolved" : newStatus === "IN_PROGRESS" ? "In Progress" : "False Positive";
    setLastActionMsg(`Anomaly ${id} status updated to ${statusLabel}`);
    setTimeout(() => setLastActionMsg(null), 5000);

    loadAnomalies();
  };

  const filteredAnomalies = anomalies.filter((anomaly) => {
    // Status Filter
    if (statusFilter !== "All") {
      const s = anomaly.status.toLowerCase();
      const target = statusFilter.toLowerCase();
      if (s !== target) return false;
    }

    // Severity Filter
    if (severityFilter !== "All") {
      if (severityFilter === "Critical" && anomaly.severityScore < 80) return false;
      if (severityFilter === "High" && (anomaly.severityScore < 50 || anomaly.severityScore >= 80)) return false;
      if (severityFilter === "Medium" && (anomaly.severityScore < 20 || anomaly.severityScore >= 50)) return false;
      if (severityFilter === "Low" && anomaly.severityScore >= 20) return false;
    }

    // Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchesId = anomaly.id.toLowerCase().includes(q);
      const matchesType = anomaly.anomalyType.toLowerCase().includes(q);
      const matchesSource = anomaly.source.toLowerCase().includes(q);
      const matchesDesc = anomaly.description ? anomaly.description.toLowerCase().includes(q) : false;
      if (!matchesId && !matchesType && !matchesSource && !matchesDesc) return false;
    }

    return true;
  });

  const columns: Column<Anomaly>[] = [
    {
      key: "id",
      label: "ID",
      sortable: true,
      className: "font-mono text-xs font-semibold text-slate-900",
    },
    {
      key: "source",
      label: "Source",
      sortable: true,
      render: (row) => <Badge variant="default">{row.source}</Badge>,
    },
    {
      key: "anomalyType",
      label: "Anomaly Type",
      sortable: true,
      render: (row) => <Badge variant="warning">{row.anomalyType}</Badge>,
    },
    {
      key: "severityScore",
      label: "Severity",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <div className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${getSeverityColor(row.severityScore)}`}>
            {row.severityScore}
          </div>
          <span className="text-xs text-slate-600 font-medium">
            {row.severityScore >= 80 ? "Critical" : row.severityScore >= 50 ? "High" : row.severityScore >= 20 ? "Medium" : "Low"}
          </span>
        </div>
      ),
    },
    {
      key: "affectedRecords",
      label: "Affected Records",
      sortable: true,
      render: (row) => (
        <span className="font-mono text-slate-700 text-xs">
          {row.affectedRecords ? formatNumber(row.affectedRecords) : "-"}
        </span>
      ),
    },
    {
      key: "detectedTime",
      label: "Detected",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
          <span>{formatDate(row.detectedTime)}</span>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
  ];

  const openCount = anomalies.filter((a) => a.status === "open" || a.status === "investigating").length;
  const criticalCount = anomalies.filter((a) => a.severityScore >= 80).length;
  const resolvedCount = anomalies.filter((a) => a.status === "resolved").length;

  return (
    <div className="space-y-6">
      {/* Top Title & Realtime Live Stream Toggle */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Anomaly Detection & Analysis</h1>

            {/* Live Streaming Badge */}
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              isLiveSync ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-slate-100 border-slate-200 text-slate-600"
            }`}>
              <span className={`w-2 h-2 rounded-full ${isLiveSync ? "bg-emerald-500 animate-ping" : "bg-slate-400"}`} />
              <span className={`w-2 h-2 rounded-full absolute ${isLiveSync ? "bg-emerald-500" : "bg-slate-400"}`} />
              <span className="ml-2 font-mono uppercase tracking-wider">{isLiveSync ? "LIVE POLLING ACTIVE" : "SYNC PAUSED"}</span>
            </div>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Realtime AI/ML detection queue for newly ingested prior-authorization and claims anomalies
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsLiveSync(!isLiveSync)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
              isLiveSync ? "bg-emerald-50 border-emerald-300 text-emerald-700" : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${isLiveSync ? "text-emerald-600 animate-pulse" : "text-slate-400"}`} />
            <span>{isLiveSync ? "Realtime Feed: ON" : "Turn Realtime Feed ON"}</span>
          </button>

          <button
            onClick={() => loadAnomalies()}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-xs transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>Refresh Now</span>
          </button>
        </div>
      </div>

      {lastActionMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-xs animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-semibold">{lastActionMsg}</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-mono">Updated live</span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Anomalies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 font-mono">{anomalies.length}</div>
            <p className="text-xs text-slate-400 mt-1">Ingested anomaly records</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Open / Investigating
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600 font-mono">{openCount}</div>
            <p className="text-xs text-amber-600 mt-1 font-medium flex items-center gap-1">
              <Activity className="w-3 h-3 animate-pulse" /> Awaiting review & resolution
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Critical Severity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-rose-600 font-mono">{criticalCount}</div>
            <p className="text-xs text-rose-600 mt-1 font-medium flex items-center gap-1">
              <ShieldAlert className="w-3 h-3" /> Isolation Forest &gt;80 score
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Resolved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 font-mono">{resolvedCount}</div>
            <p className="text-xs text-emerald-600 mt-1 font-medium flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Successfully remediated
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Table */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-4 border-b border-slate-100">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <span>Detected Anomalies</span>
                <span className="text-xs font-normal text-slate-400 font-mono">({filteredAnomalies.length} records)</span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                Click any anomaly row to inspect root-cause attribution and trigger workflow actions
              </CardDescription>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search anomaly ID, type, or source..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 text-slate-700 w-64"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          {/* Status & Severity Filter Badges */}
          <div className="space-y-2 pb-2 border-b border-slate-100">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1">Status:</span>
              {["All", "open", "investigating", "resolved", "false_positive"].map((status) => {
                const count = status === "All" ? anomalies.length : anomalies.filter((a) => a.status === status).length;
                return (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                      statusFilter === status
                        ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs"
                        : "bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {status === "All" ? "All Statuses" : status}
                    <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] bg-slate-200/60 text-slate-700">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1">Severity:</span>
              {["All", "Critical", "High", "Medium", "Low"].map((severity) => (
                <button
                  key={severity}
                  onClick={() => setSeverityFilter(severity)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    severityFilter === severity
                      ? "bg-slate-900 text-white shadow-2xs"
                      : "bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {severity}
                </button>
              ))}
            </div>
          </div>

          <DataTable
            data={filteredAnomalies}
            columns={columns}
            onRowClick={(row) => setSelectedAnomaly(row)}
          />
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedAnomaly && (
        <Modal
          isOpen={!!selectedAnomaly}
          onClose={() => setSelectedAnomaly(null)}
          title="Anomaly Details & Diagnostic View"
          size="lg"
        >
          <div className="space-y-6">
            {/* Header */}
            <div>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                    <span>{selectedAnomaly.anomalyType}</span>
                    <Badge variant="warning">{selectedAnomaly.source}</Badge>
                  </h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">{selectedAnomaly.id}</p>
                </div>
                <StatusBadge status={selectedAnomaly.status} />
              </div>
              <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200">
                {selectedAnomaly.description}
              </p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Severity Score</div>
                <div className={`text-2xl font-bold font-mono ${getSeverityColor(selectedAnomaly.severityScore)}`}>
                  {selectedAnomaly.severityScore}
                </div>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Affected Records</div>
                <div className="text-2xl font-bold text-slate-800 font-mono">
                  {selectedAnomaly.affectedRecords ? formatNumber(selectedAnomaly.affectedRecords) : "1 Record"}
                </div>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Detected Time</div>
                <div className="text-xs font-semibold text-slate-800 font-mono mt-1">
                  {formatDate(selectedAnomaly.detectedTime)}
                </div>
              </div>
            </div>

            {/* Root Cause & RAG Analysis */}
            {selectedAnomaly.rootCause && (
              <div>
                <h4 className="font-bold text-xs uppercase tracking-wider mb-2 flex items-center gap-2 text-slate-900">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Isolation Forest & RAG Root Cause Attribution
                </h4>
                <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl">
                  <p className="text-xs text-amber-900 leading-relaxed font-sans">{selectedAnomaly.rootCause}</p>
                </div>
              </div>
            )}

            {/* Consolidated Architecture Data Box */}
            <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-blue-900 flex items-center gap-2">
                <Cpu className="h-4 w-4 text-blue-600" />
                Pipeline Scoring Metrics
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="p-2.5 bg-white rounded-lg border border-blue-200/60">
                  <span className="text-slate-500 block text-[11px]">Source Feed:</span>
                  <span className="font-bold text-slate-800 font-mono">{selectedAnomaly.source}</span>
                </div>
                <div className="p-2.5 bg-white rounded-lg border border-blue-200/60">
                  <span className="text-slate-500 block text-[11px]">Detection Engine:</span>
                  <span className="font-bold text-blue-700 font-mono">
                    {selectedAnomaly.source === "AUTHORIZATION" || selectedAnomaly.source === "Authorization"
                      ? "Isolation Forest ML"
                      : "Rule-Based Engine"}
                  </span>
                </div>
                <div className="p-2.5 bg-white rounded-lg border border-blue-200/60">
                  <span className="text-slate-500 block text-[11px]">Risk Rating:</span>
                  <span className="font-bold text-rose-600 font-mono">
                    {selectedAnomaly.severityScore >= 80 ? "Critical Outlier" : selectedAnomaly.severityScore >= 50 ? "High Risk" : "Moderate Risk"}
                  </span>
                </div>
                <div className="p-2.5 bg-white rounded-lg border border-blue-200/60">
                  <span className="text-slate-500 block text-[11px]">SLA Target:</span>
                  <span className="font-bold text-slate-800 font-mono">24.0 Hours</span>
                </div>
              </div>
            </div>

            {/* Impact Analysis */}
            {selectedAnomaly.impactAnalysis && (
              <div>
                <h4 className="font-bold text-xs uppercase tracking-wider mb-3 flex items-center gap-2 text-slate-900">
                  <Activity className="h-4 w-4 text-blue-600" />
                  Impact & Business Exposure Analysis
                </h4>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 border border-slate-200 rounded-xl bg-white">
                      <div className="text-xs text-slate-500 mb-1">Affected Volume</div>
                      <div className="text-lg font-bold text-slate-800 font-mono">
                        {formatNumber(selectedAnomaly.impactAnalysis.affectedClaimsCount)}
                      </div>
                    </div>
                    <div className="p-3 border border-slate-200 rounded-xl bg-white">
                      <div className="text-xs text-slate-500 mb-1">Estimated Impact</div>
                      <div className="text-lg font-bold text-slate-800 font-mono">
                        {formatNumber(selectedAnomaly.impactAnalysis.estimatedVolumeImpact)}
                      </div>
                    </div>
                  </div>

                  {selectedAnomaly.impactAnalysis.financialImpact && (
                    <div className="p-3 border border-slate-200 rounded-xl flex items-center gap-2 bg-white">
                      <DollarSign className="h-5 w-5 text-emerald-600" />
                      <div>
                        <div className="text-xs text-slate-500">Financial Exposure</div>
                        <div className="text-lg font-bold text-slate-800 font-mono">
                          ${formatNumber(selectedAnomaly.impactAnalysis.financialImpact)}
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="text-xs text-slate-500 mb-1 font-medium">Business Impact Summary</div>
                    <p className="text-xs text-slate-700 p-2.5 bg-slate-50 rounded-lg border border-slate-200">{selectedAnomaly.impactAnalysis.businessImpact}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Workflow Action Buttons */}
            <div className="pt-4 border-t border-slate-200 flex flex-wrap gap-2.5 justify-end">
              <button
                type="button"
                onClick={() => handleStatusChange(selectedAnomaly.id, "IGNORED")}
                className="px-3.5 py-2 border border-slate-200 hover:bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold transition-all"
              >
                Mark False Positive
              </button>

              <button
                type="button"
                onClick={() => handleStatusChange(selectedAnomaly.id, "IN_PROGRESS")}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all"
              >
                Assign to Review Queue
              </button>

              <button
                type="button"
                onClick={() => handleStatusChange(selectedAnomaly.id, "RESOLVED")}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all"
              >
                Mark as Resolved
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
