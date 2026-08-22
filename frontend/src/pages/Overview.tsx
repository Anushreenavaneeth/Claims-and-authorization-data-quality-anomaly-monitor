import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from "recharts";
import { getDashboardSummary, getTrends } from "../services/integratedApi";
import { formatNumber, formatPercentage } from "../lib/utils";
import { TrendingUp, TrendingDown, AlertCircle, Clock, CheckCircle2, RefreshCw } from "lucide-react";
import type { DashboardSummary, TrendData } from "../types/integrated";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e"];

export function Overview() {
  const [summary, setSummary]     = useState<DashboardSummary | null>(null);
  const [trends,  setTrends]      = useState<TrendData | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error,   setError]       = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([getDashboardSummary(), getTrends()])
      .then(([s, t]) => { setSummary(s); setTrends(t); })
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? "Failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  // Build severity pie data from real data
  const severityData = trends
    ? Object.entries(trends.severity_distribution).map(([k, v]) => ({ date: k, value: v }))
    : [];

  // Build dataset health cards from real data
  const datasets = trends?.datasets ?? [];

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="flex items-center gap-2 text-muted-foreground">
        <RefreshCw className="h-5 w-5 animate-spin" />
        Loading dashboard…
      </div>
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">{error}</p>
        <button onClick={load} className="mt-3 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm">
          Retry
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Overview Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Real-time monitoring across Claims, Authorization &amp; Pharmacy
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 text-sm"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Records</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(summary?.total_records ?? 0)}</div>
            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
              <TrendingUp className="h-3 w-3" /><span>3 datasets</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Quality Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(summary?.average_quality_score ?? 0)}
            </div>
            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
              <CheckCircle2 className="h-3 w-3" /><span>Avg quality index</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Open Anomalies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{formatNumber(summary?.total_anomalies ?? 0)}</div>
            <div className="flex items-center gap-1 text-xs text-orange-600 mt-1">
              <AlertCircle className="h-3 w-3" />
              <span>{formatPercentage(summary?.anomaly_rate ?? 0)} anomaly rate</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">SLA Breaches</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatNumber(summary?.sla_breaches ?? 0)}</div>
            <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
              <Clock className="h-3 w-3" /><span>Immediate action</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Critical Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(summary?.critical_issues ?? 0)}</div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
              <TrendingDown className="h-3 w-3" /><span>P1 priority</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData} cx="50%" cy="50%"
                  labelLine={false}
                  label={(e: any) => `${e.date}: ${e.value}`}
                  outerRadius={100} dataKey="value"
                >
                  {severityData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>SLA Status Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={trends ? Object.entries(trends.sla_distribution).map(([k, v]) => ({ name: k, value: v })) : []}
                  cx="50%" cy="50%" outerRadius={100} dataKey="value"
                  label={(e: any) => `${e.name}: ${e.value}`}
                >
                  {["#ef4444", "#f97316", "#eab308", "#22c55e"].map((c, i) => (
                    <Cell key={i} fill={c} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Dataset Health */}
      <Card>
        <CardHeader><CardTitle>Dataset Health</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {datasets.map((ds) => {
              const anomalyRate = ds.total > 0 ? (ds.anomalies / ds.total) * 100 : 0;
              const status = anomalyRate > 50 ? "error" : anomalyRate > 20 ? "warning" : "healthy";
              return (
                <div key={ds.dataset} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold capitalize">{ds.dataset}</h4>
                      <p className="text-xs text-muted-foreground">Data pipeline</p>
                    </div>
                    <StatusBadge status={status} />
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Records:</span>
                      <span className="font-medium">{formatNumber(ds.total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Anomalies:</span>
                      <span className="font-medium text-orange-600">{formatNumber(ds.anomalies)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Anomaly Rate:</span>
                      <span className="font-medium">{formatPercentage(anomalyRate)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                      <div
                        className={`h-1.5 rounded-full ${anomalyRate > 50 ? "bg-red-500" : anomalyRate > 20 ? "bg-yellow-500" : "bg-green-500"}`}
                        style={{ width: `${Math.min(anomalyRate, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Severity + SLA summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Critical", value: summary?.critical_issues ?? 0, color: "text-red-600" },
          { label: "High",     value: summary?.high_issues     ?? 0, color: "text-orange-600" },
          { label: "Medium",   value: summary?.medium_issues   ?? 0, color: "text-yellow-600" },
          { label: "Low",      value: summary?.low_issues      ?? 0, color: "text-green-600" },
        ].map(({ label, value, color }) => (
          <Card key={label}>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">{label} Issues</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${color}`}>{formatNumber(value)}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
