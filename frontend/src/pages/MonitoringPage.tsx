import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { getDashboardSummary, getTrends, getRootCauses } from "../services/integratedApi";
import { formatNumber, formatPercentage } from "../lib/utils";
import { Download, TrendingUp, Clock, AlertTriangle } from "lucide-react";
import type { DashboardSummary, TrendData } from "../types/integrated";

const COLORS = ["#ef4444","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6"];

export function MonitoringPage() {
  const [summary,    setSummary]    = useState<DashboardSummary | null>(null);
  const [trends,     setTrends]     = useState<TrendData | null>(null);
  const [rootCauses, setRootCauses] = useState<{rule:string;count:number}[]>([]);
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    Promise.all([getDashboardSummary(), getTrends(), getRootCauses()])
      .then(([s, t, rc]) => { setSummary(s); setTrends(t); setRootCauses(rc.root_causes ?? []); })
      .finally(() => setLoading(false));
  }, []);

  const severityData = trends
    ? Object.entries(trends.severity_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const slaData = trends
    ? Object.entries(trends.sla_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const datasetData = (trends?.datasets ?? []).map(d => ({
    name: d.dataset, anomalies: d.anomalies, normal: d.total - d.anomalies,
  }));

  const rcData = rootCauses.slice(0, 8).map(r => ({
    name: r.rule.replace(/_/g, " ").slice(0, 25), count: r.count,
  }));

  const handleExportCSV = () => {
    if (!summary) return;
    const csv = [
      ["Metric","Value"],
      ["Total Records",   summary.total_records],
      ["Total Anomalies", summary.total_anomalies],
      ["Anomaly Rate",    `${summary.anomaly_rate}%`],
      ["SLA Breaches",    summary.sla_breaches],
      ["SLA At Risk",     summary.sla_at_risk],
      ["Avg Quality",     `${summary.average_quality_score}%`],
    ].map(r => r.join(",")).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `monitoring-${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading monitoring data…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Monitoring Dashboard</h1>
          <p className="text-muted-foreground mt-1">Comprehensive reporting and trend analysis</p>
        </div>
        <button onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2 border rounded-md text-sm hover:bg-accent">
          <Download className="h-4 w-4" />Export CSV
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><TrendingUp className="h-4 w-4"/>Total Anomalies</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{formatNumber(summary?.total_anomalies??0)}</div><p className="text-xs text-muted-foreground mt-1">All datasets</p></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><Clock className="h-4 w-4"/>Anomaly Rate</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-orange-600">{formatPercentage(summary?.anomaly_rate??0)}</div><p className="text-xs text-muted-foreground mt-1">Of total records</p></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Avg Quality Score</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-600">{formatPercentage(summary?.average_quality_score??0)}</div><p className="text-xs text-muted-foreground mt-1">Data quality index</p></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2"><AlertTriangle className="h-4 w-4"/>Critical Issues</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-600">{formatNumber(summary?.critical_issues??0)}</div><p className="text-xs text-muted-foreground mt-1">Severity CRITICAL</p></CardContent></Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle>Anomalies by Dataset</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={datasetData}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis />
                <Tooltip /><Legend />
                <Bar dataKey="anomalies" fill="#ef4444" name="Anomalies" />
                <Bar dataKey="normal"    fill="#22c55e" name="Normal"    />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card><CardHeader><CardTitle>Severity Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" outerRadius={100} dataKey="value"
                     label={(e:any)=>`${e.name}: ${e.value}`}>
                  {severityData.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card><CardHeader><CardTitle>SLA Status Distribution</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={slaData} cx="50%" cy="50%" outerRadius={100} dataKey="value"
                     label={(e:any)=>`${e.name}: ${e.value}`}>
                  {slaData.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card><CardHeader><CardTitle>Top Root Causes</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={rcData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" /><YAxis type="category" dataKey="name" width={130} tick={{fontSize:10}} />
                <Tooltip /><Bar dataKey="count" fill="#8b5cf6" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Executive Summary */}
      <Card><CardHeader><CardTitle>Executive Summary</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4 text-sm">
            <div>
              <h4 className="font-semibold mb-1">Overall Status</h4>
              <p className="text-muted-foreground">
                {formatNumber(summary?.total_records ?? 0)} records processed across 3 datasets.
                Average data quality score is {formatPercentage(summary?.average_quality_score ?? 0)}.
                Anomaly rate of {formatPercentage(summary?.anomaly_rate ?? 0)} detected.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">SLA Compliance</h4>
              <p className="text-muted-foreground">
                {formatNumber(summary?.sla_breaches ?? 0)} SLA breaches and {formatNumber(summary?.sla_at_risk ?? 0)} at-risk records
                require immediate attention. {summary?.critical_issues} critical issues require P1 (1-hour) response.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">Key Findings</h4>
              <ul className="list-disc list-inside text-muted-foreground space-y-1">
                <li>CRITICAL: {formatNumber(summary?.critical_issues ?? 0)} records</li>
                <li>HIGH: {formatNumber(summary?.high_issues ?? 0)} records</li>
                <li>MEDIUM: {formatNumber(summary?.medium_issues ?? 0)} records</li>
                <li>TOP root cause: {rootCauses[0]?.rule?.replace(/_/g," ") ?? "N/A"} ({rootCauses[0]?.count ?? 0} occurrences)</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
