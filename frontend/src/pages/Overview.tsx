import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  getDashboardSummary,
  getAnomalyTrends,
  getSeverityBreakdown,
  getDataSources,
  getAnomalies,
  updateAnomalyStatus,
} from "../services/api";
import { formatNumber, formatPercentage } from "../lib/utils";
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Clock,
  CheckCircle2,
  Briefcase,
  ArrowRight,
  ShieldCheck,
  FileCheck,
} from "lucide-react";
import type { DashboardSummary, TimeSeriesData, DataSource, Anomaly } from "../types";
import { useAuth } from "../auth/AuthContext";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e"];

export function Overview() {
  const { user, isWorker } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TimeSeriesData[]>([]);
  const [severity, setSeverity] = useState<TimeSeriesData[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [workerAnomalies, setWorkerAnomalies] = useState<Anomaly[]>([]);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = async () => {
    const [summaryData, trendsData, severityData, sourcesData, anomaliesData] = await Promise.all([
      getDashboardSummary(),
      getAnomalyTrends(),
      getSeverityBreakdown(),
      getDataSources(),
      getAnomalies(),
    ]);

    setSummary(summaryData);
    setTrends(trendsData);
    setSeverity(severityData);
    setSources(sourcesData);
    setWorkerAnomalies(anomaliesData.slice(0, 8));
  };

  const handleQuickResolve = async (id: string) => {
    setResolvingId(id);
    try {
      await updateAnomalyStatus(id, "RESOLVED");
      loadData();
    } finally {
      setResolvingId(null);
    }
  };

  if (!summary) {
    return <div className="flex items-center justify-center h-full text-xs font-mono">Loading dashboard telemetry…</div>;
  }

  // ──────────────────────────────────────────────────────────────────────────
  // WORKER OPERATIONAL WORKSPACE
  // ──────────────────────────────────────────────────────────────────────────
  if (isWorker) {
    const openCount = workerAnomalies.filter((a) => a.status === "open").length;
    const investigatingCount = workerAnomalies.filter((a) => a.status === "investigating").length;
    const resolvedCount = workerAnomalies.filter((a) => a.status === "resolved").length;

    return (
      <div className="space-y-6">
        {/* Worker Header Banner */}
        <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-950/60 via-slate-900 to-cyan-950/50 border border-blue-500/25 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 flex items-center justify-center font-bold text-lg">
              <Briefcase className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">
                Welcome back, {user?.name || "Data Steward"}
              </h1>
              <p className="text-xs font-mono text-cyan-300/70 mt-0.5">
                Claims & Pre-Authorization Data Operations Work Queue
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/review"
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-mono font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow"
            >
              Start Review Queue <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Worker KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Action Items Awaiting Fix
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-500 font-mono">{openCount}</div>
              <p className="text-[11px] font-mono text-muted-foreground mt-1">Requires clinical / data edit</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Under Investigation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-400 font-mono">{investigatingCount}</div>
              <p className="text-[11px] font-mono text-muted-foreground mt-1">In progress corrections</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                Resolved Today
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400 font-mono">{resolvedCount}</div>
              <p className="text-[11px] font-mono text-muted-foreground mt-1">Audited & verified</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-mono uppercase text-muted-foreground">
                SLA Compliance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-400 font-mono">98.4%</div>
              <p className="text-[11px] font-mono text-emerald-400 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> On track within 4h window
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Assigned Anomalies Work Queue */}
        <Card className="rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-border bg-muted/20 flex flex-row items-center justify-between py-4">
            <div>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-primary" />
                Assigned Anomaly Action Queue
              </CardTitle>
              <p className="text-xs font-mono text-muted-foreground mt-0.5">
                Review root causes, apply recommended SOP corrections, and close tickets.
              </p>
            </div>
            <Link
              to="/anomalies"
              className="text-xs font-mono text-primary hover:underline flex items-center gap-1"
            >
              View All Anomalies →
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-muted/40 border-b border-border text-muted-foreground uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Source & ID</th>
                    <th className="px-4 py-3">Anomaly Type</th>
                    <th className="px-4 py-3">Risk Level</th>
                    <th className="px-4 py-3">Root Cause & Recommended Fix</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Quick Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {workerAnomalies.map((a) => (
                    <tr key={a.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3 font-medium text-foreground">
                        <span className="font-bold text-foreground font-sans block">{a.source}</span>
                        <span className="text-[10px] text-muted-foreground">{a.id.slice(0, 12)}…</span>
                      </td>
                      <td className="px-4 py-3 text-foreground font-medium">{a.anomalyType}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            a.severityScore >= 70
                              ? "bg-red-500/15 text-red-400 border border-red-500/30"
                              : a.severityScore >= 40
                              ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                              : "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                          }`}
                        >
                          {a.severityScore >= 70 ? "HIGH RISK" : a.severityScore >= 40 ? "MEDIUM RISK" : "LOW RISK"}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-sm">
                        <p className="text-foreground truncate">{a.description}</p>
                        {a.rootCause && (
                          <p className="text-[10px] text-muted-foreground truncate mt-0.5">
                            💡 {a.rootCause}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] ${
                            a.status === "resolved"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : a.status === "investigating"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              : "bg-orange-500/10 text-orange-400 border border-orange-500/20"
                          }`}
                        >
                          {a.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {a.status !== "resolved" ? (
                          <button
                            onClick={() => handleQuickResolve(a.id)}
                            disabled={resolvingId === a.id}
                            className="inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-mono font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm disabled:opacity-50"
                          >
                            <ShieldCheck className="w-3.5 h-3.5" />
                            {resolvingId === a.id ? "Resolving…" : "Resolve"}
                          </button>
                        ) : (
                          <span className="text-[11px] text-emerald-400 flex items-center justify-end gap-1 font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // ADMIN PLATFORM HEALTH OVERVIEW
  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Platform Overview & Telemetry</h1>
        <p className="text-muted-foreground mt-1">
          Executive monitoring of data quality, claim pipelines, and anomaly detection engines.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Records Processed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(summary.totalRecordsProcessed)}</div>
            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
              <TrendingUp className="h-3 w-3" />
              <span>+12.5% from last week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Quality Pass Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(summary.dataQualityPassRate)}
            </div>
            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
              <CheckCircle2 className="h-3 w-3" />
              <span>Excellent</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Open Anomalies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{summary.openAnomalies}</div>
            <div className="flex items-center gap-1 text-xs text-orange-600 mt-1">
              <AlertCircle className="h-3 w-3" />
              <span>Requires attention</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              SLA Breaches
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{summary.slaBreaches}</div>
            <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
              <Clock className="h-3 w-3" />
              <span>Critical</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Resolution Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.avgResolutionTime}h</div>
            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
              <TrendingDown className="h-3 w-3" />
              <span>-8% improvement</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomaly Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Anomaly Trends (Last 14 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => {
                    const dateValue = value as string;
                    return new Date(dateValue).toLocaleDateString();
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Anomalies"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Severity Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Anomaly Severity Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severity}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.date}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severity.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Data Source Health */}
      <Card>
        <CardHeader>
          <CardTitle>Data Source Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {sources.map((source) => (
              <div
                key={source.id}
                className="p-4 border rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold">{source.name}</h4>
                    <p className="text-xs text-muted-foreground">{source.subType}</p>
                  </div>
                  <StatusBadge status={source.status} />
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Records:</span>
                    <span className="font-medium">{formatNumber(source.recordCount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Errors:</span>
                    <span className="font-medium text-red-600">{source.errorCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Last Sync:</span>
                    <span className="font-medium text-xs">
                      {new Date(source.lastSync).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
