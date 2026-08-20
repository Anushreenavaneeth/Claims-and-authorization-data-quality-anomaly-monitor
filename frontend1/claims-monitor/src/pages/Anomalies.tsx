import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Modal } from "../components/ui/Modal";
import { Badge } from "../components/ui/Badge";
import { getAnomalies } from "../services/api";
import { formatNumber, formatDate, getSeverityColor } from "../lib/utils";
import { AlertTriangle, DollarSign, Activity } from "lucide-react";
import type { Anomaly } from "../types";

export function Anomalies() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [severityFilter, setSeverityFilter] = useState<string>("All");

  useEffect(() => {
    loadAnomalies();
  }, []);

  const loadAnomalies = async () => {
    const data = await getAnomalies();
    setAnomalies(data);
  };

  const filteredAnomalies = anomalies.filter((anomaly) => {
    if (statusFilter !== "All" && anomaly.status !== statusFilter) return false;
    if (severityFilter !== "All") {
      if (severityFilter === "Critical" && anomaly.severityScore < 80) return false;
      if (severityFilter === "High" && (anomaly.severityScore < 50 || anomaly.severityScore >= 80)) return false;
      if (severityFilter === "Medium" && (anomaly.severityScore < 20 || anomaly.severityScore >= 50)) return false;
      if (severityFilter === "Low" && anomaly.severityScore >= 20) return false;
    }
    return true;
  });

  const columns: Column<Anomaly>[] = [
    {
      key: "id",
      label: "ID",
      sortable: true,
      className: "font-mono text-xs",
    },
    {
      key: "source",
      label: "Source",
      sortable: true,
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
          <div className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(row.severityScore)}`}>
            {row.severityScore}
          </div>
          <span className="text-xs text-muted-foreground">
            {row.severityScore >= 80 ? "Critical" : row.severityScore >= 50 ? "High" : row.severityScore >= 20 ? "Medium" : "Low"}
          </span>
        </div>
      ),
    },
    {
      key: "affectedRecords",
      label: "Affected Records",
      sortable: true,
      render: (row) => row.affectedRecords ? formatNumber(row.affectedRecords) : "-",
    },
    {
      key: "detectedTime",
      label: "Detected",
      sortable: true,
      render: (row) => <span className="text-xs">{formatDate(row.detectedTime)}</span>,
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Anomaly Detection & Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Review and analyze detected data anomalies
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Anomalies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{anomalies.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Open / Investigating
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {anomalies.filter((a) => a.status === "open" || a.status === "investigating").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Critical Severity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {anomalies.filter((a) => a.severityScore >= 80).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Resolved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {anomalies.filter((a) => a.status === "resolved").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detected Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="mb-4 space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              {["All", "open", "investigating", "resolved", "false_positive"].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    statusFilter === status
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary hover:bg-secondary/80"
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Severity:</span>
              {["All", "Critical", "High", "Medium", "Low"].map((severity) => (
                <button
                  key={severity}
                  onClick={() => setSeverityFilter(severity)}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    severityFilter === severity
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary hover:bg-secondary/80"
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
          title="Anomaly Details"
          size="lg"
        >
          <div className="space-y-6">
            {/* Header */}
            <div>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-xl font-semibold">{selectedAnomaly.anomalyType}</h3>
                  <p className="text-sm text-muted-foreground">{selectedAnomaly.id}</p>
                </div>
                <StatusBadge status={selectedAnomaly.status} />
              </div>
              <p className="text-sm">{selectedAnomaly.description}</p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Severity Score</div>
                <div className={`text-2xl font-bold ${getSeverityColor(selectedAnomaly.severityScore)}`}>
                  {selectedAnomaly.severityScore}
                </div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Affected Records</div>
                <div className="text-2xl font-bold">
                  {selectedAnomaly.affectedRecords ? formatNumber(selectedAnomaly.affectedRecords) : "N/A"}
                </div>
              </div>
              <div className="p-3 bg-muted rounded-lg">
                <div className="text-xs text-muted-foreground mb-1">Detected</div>
                <div className="text-sm font-medium">
                  {formatDate(selectedAnomaly.detectedTime)}
                </div>
              </div>
            </div>

            {/* Root Cause Analysis */}
            {selectedAnomaly.rootCause && (
              <div>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Root Cause Analysis
                </h4>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm">{selectedAnomaly.rootCause}</p>
                </div>
              </div>
            )}

            {/* Impact Analysis */}
            {selectedAnomaly.impactAnalysis && (
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Impact Analysis
                </h4>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 border rounded-lg">
                      <div className="text-xs text-muted-foreground mb-1">Affected Claims</div>
                      <div className="text-lg font-semibold">
                        {formatNumber(selectedAnomaly.impactAnalysis.affectedClaimsCount)}
                      </div>
                    </div>
                    <div className="p-3 border rounded-lg">
                      <div className="text-xs text-muted-foreground mb-1">Volume Impact</div>
                      <div className="text-lg font-semibold">
                        {formatNumber(selectedAnomaly.impactAnalysis.estimatedVolumeImpact)}
                      </div>
                    </div>
                  </div>
                  
                  {selectedAnomaly.impactAnalysis.financialImpact && (
                    <div className="p-3 border rounded-lg flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="text-xs text-muted-foreground">Financial Impact</div>
                        <div className="text-lg font-semibold">
                          ${formatNumber(selectedAnomaly.impactAnalysis.financialImpact)}
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="text-xs text-muted-foreground mb-2">Business Impact</div>
                    <p className="text-sm">{selectedAnomaly.impactAnalysis.businessImpact}</p>
                  </div>

                  <div>
                    <div className="text-xs text-muted-foreground mb-2">Downstream Systems Affected</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedAnomaly.impactAnalysis.downstreamSystems.map((system) => (
                        <Badge key={system} variant="info">{system}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
