import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  getAnomalyTrends,
  getSeverityBreakdown,
  getSLAItems,
  getAnomalies,
} from "../services/api";
import { formatPercentage } from "../lib/utils";
import { Download, TrendingUp, Clock, AlertTriangle } from "lucide-react";
import type { TimeSeriesData, SLAItem, Anomaly } from "../types";

export function Monitoring() {
  const [anomalyTrends, setAnomalyTrends] = useState<TimeSeriesData[]>([]);
  const [severityData, setSeverityData] = useState<TimeSeriesData[]>([]);
  const [slaItems, setSlaItems] = useState<SLAItem[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [trends, severity, sla, anom] = await Promise.all([
      getAnomalyTrends(),
      getSeverityBreakdown(),
      getSLAItems(),
      getAnomalies(),
    ]);
    setAnomalyTrends(trends);
    setSeverityData(severity);
    setSlaItems(sla);
    setAnomalies(anom);
  };

  // Calculate resolution time trends (mock data for demonstration)
  const resolutionTimeTrends: TimeSeriesData[] = [
    { date: "Week 1", value: 5.2 },
    { date: "Week 2", value: 4.8 },
    { date: "Week 3", value: 4.5 },
    { date: "Week 4", value: 4.2 },
  ];

  // Anomaly by type breakdown
  const anomalyByType = anomalies.reduce((acc, anomaly) => {
    const existing = acc.find((item) => item.date === anomaly.anomalyType);
    if (existing) {
      existing.value++;
    } else {
      acc.push({ date: anomaly.anomalyType, value: 1 });
    }
    return acc;
  }, [] as TimeSeriesData[]);

  // SLA compliance percentage
  const slaCompliance = slaItems.length > 0
    ? ((slaItems.filter((item) => item.status !== "breached").length / slaItems.length) * 100)
    : 100;

  const handleExportCSV = () => {
    const csvContent = [
      ["Metric", "Value"],
      ["Total Anomalies", anomalies.length],
      ["SLA Compliance", `${slaCompliance.toFixed(1)}%`],
      ["Average Resolution Time", "4.2 hours"],
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `monitoring-report-${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  const handleExportPDF = () => {
    alert("PDF export would be implemented with a library like jsPDF or server-side generation");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Monitoring Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive reporting and trend analysis
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleExportCSV}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportPDF}>
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Total Anomalies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{anomalies.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              SLA Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(slaCompliance)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Target: 95%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Resolution Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2h</div>
            <p className="text-xs text-green-600 mt-1">↓ 8% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Critical Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {anomalies.filter((a) => a.severityScore >= 80).length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Severity ≥ 80</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomaly Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Anomaly Trends (14 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={anomalyTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })
                  }
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
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Resolution Time Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Resolution Time Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={resolutionTimeTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: "Hours", angle: -90, position: "insideLeft" }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Avg Hours"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Anomaly by Type */}
        <Card>
          <CardHeader>
            <CardTitle>Anomalies by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={anomalyByType}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8b5cf6" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Severity Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Severity Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#f59e0b" name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Summary Report */}
      <Card>
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none">
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Overall Data Quality Status</h4>
                <p className="text-muted-foreground">
                  The data quality pass rate remains excellent at 96.8%, with {anomalies.length} anomalies
                  detected in the last 30 days. The system is currently processing over 1.2M records daily
                  across 4 data sources.
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-2">SLA Compliance</h4>
                <p className="text-muted-foreground">
                  SLA compliance is at {formatPercentage(slaCompliance)}, {slaCompliance >= 95 ? "meeting" : "below"} the 95% target.
                  Average resolution time has improved by 8% compared to last month, now at 4.2 hours.
                  {slaItems.filter((item) => item.status === "breached").length > 0 && (
                    <span className="text-red-600">
                      {" "}
                      There are currently {slaItems.filter((item) => item.status === "breached").length} breached SLAs requiring immediate attention.
                    </span>
                  )}
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Key Findings</h4>
                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                  <li>
                    Critical anomalies ({anomalies.filter((a) => a.severityScore >= 80).length}) primarily
                    affecting Claims and Authorization data sources
                  </li>
                  <li>
                    Most common anomaly types: Duplicate Claims Spike, Missing NPI Data, and Approval Workflow
                    Timeouts
                  </li>
                  <li>
                    High-confidence recommendations available for immediate execution
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Recommendations</h4>
                <ol className="list-decimal list-inside text-muted-foreground space-y-1">
                  <li>Prioritize resolution of breached SLA items in Authorization system</li>
                  <li>Implement additional validation rules for duplicate claim detection</li>
                  <li>Schedule review of NPI validation service integration with external provider</li>
                </ol>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
