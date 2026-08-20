import { useEffect, useState } from "react";
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
} from "../services/api";
import { formatNumber, formatPercentage } from "../lib/utils";
import { TrendingUp, TrendingDown, AlertCircle, Clock, CheckCircle2 } from "lucide-react";
import type { DashboardSummary, TimeSeriesData, DataSource } from "../types";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e"];

export function Overview() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TimeSeriesData[]>([]);
  const [severity, setSeverity] = useState<TimeSeriesData[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [summaryData, trendsData, severityData, sourcesData] = await Promise.all([
      getDashboardSummary(),
      getAnomalyTrends(),
      getSeverityBreakdown(),
      getDataSources(),
    ]);

    setSummary(summaryData);
    setTrends(trendsData);
    setSeverity(severityData);
    setSources(sourcesData);
  };

  if (!summary) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Overview Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Real-time monitoring of data quality and anomaly detection
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
