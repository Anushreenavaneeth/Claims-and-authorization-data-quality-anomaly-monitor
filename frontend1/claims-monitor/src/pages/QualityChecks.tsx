import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Badge } from "../components/ui/Badge";
import { getQualityChecks, getQuarantinedRecords } from "../services/api";
import { formatNumber, formatPercentage, formatDate } from "../lib/utils";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import type { QualityCheck, QuarantinedRecord, QualityCheckType } from "../types";

export function QualityChecks() {
  const [checks, setChecks] = useState<QualityCheck[]>([]);
  const [quarantined, setQuarantined] = useState<QuarantinedRecord[]>([]);
  const [selectedType, setSelectedType] = useState<QualityCheckType | "All">("All");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [checksData, quarantinedData] = await Promise.all([
      getQualityChecks(),
      getQuarantinedRecords(),
    ]);
    setChecks(checksData);
    setQuarantined(quarantinedData);
  };

  const checkTypes: (QualityCheckType | "All")[] = [
    "All",
    "Schema Validation",
    "Completeness Check",
    "Uniqueness Check",
    "Referential Integrity",
    "Business Rule Check",
  ];

  const filteredChecks =
    selectedType === "All"
      ? checks
      : checks.filter((check) => check.type === selectedType);

  const checksColumns: Column<QualityCheck>[] = [
    {
      key: "name",
      label: "Check Name",
      sortable: true,
      render: (row) => (
        <div>
          <div className="font-medium">{row.name}</div>
          {row.description && (
            <div className="text-xs text-muted-foreground">{row.description}</div>
          )}
        </div>
      ),
    },
    {
      key: "type",
      label: "Type",
      sortable: true,
      render: (row) => <Badge variant="info">{row.type}</Badge>,
    },
    {
      key: "recordsChecked",
      label: "Records Checked",
      sortable: true,
      render: (row) => formatNumber(row.recordsChecked),
    },
    {
      key: "recordsFailed",
      label: "Failed",
      sortable: true,
      render: (row) => (
        <span className={row.recordsFailed > 1000 ? "text-red-600 font-medium" : ""}>
          {formatNumber(row.recordsFailed)}
        </span>
      ),
    },
    {
      key: "passPercentage",
      label: "Pass %",
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          {row.passPercentage >= 99 ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : row.passPercentage >= 95 ? (
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          ) : (
            <XCircle className="h-4 w-4 text-red-600" />
          )}
          <span className={row.passPercentage >= 95 ? "text-green-600" : "text-red-600"}>
            {formatPercentage(row.passPercentage)}
          </span>
        </div>
      ),
    },
    {
      key: "lastRun",
      label: "Last Run",
      sortable: true,
      render: (row) => <span className="text-xs">{formatDate(row.lastRun)}</span>,
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
  ];

  const quarantineColumns: Column<QuarantinedRecord>[] = [
    {
      key: "recordId",
      label: "Record ID",
      sortable: true,
      className: "font-mono text-xs",
    },
    {
      key: "sourceType",
      label: "Source",
      sortable: true,
    },
    {
      key: "checkType",
      label: "Failed Check",
      sortable: true,
      render: (row) => <Badge variant="warning">{row.checkType}</Badge>,
    },
    {
      key: "failReason",
      label: "Reason",
      sortable: true,
      render: (row) => (
        <div className="max-w-md truncate" title={row.failReason}>
          {row.failReason}
        </div>
      ),
    },
    {
      key: "quarantinedAt",
      label: "Quarantined At",
      sortable: true,
      render: (row) => <span className="text-xs">{formatDate(row.quarantinedAt)}</span>,
    },
  ];

  const totalChecked = checks.reduce((sum, check) => sum + check.recordsChecked, 0);
  const totalFailed = checks.reduce((sum, check) => sum + check.recordsFailed, 0);
  const overallPassRate = ((totalChecked - totalFailed) / totalChecked) * 100;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Data Quality Checks</h1>
        <p className="text-muted-foreground mt-1">
          Monitor data validation and quality check results
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{checks.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Records Checked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(totalChecked)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overall Pass Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(overallPassRate)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Quarantined Records
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{quarantined.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Quality Check Results</CardTitle>
          <CardDescription>Filter by check type to view specific validations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {checkTypes.map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedType === type
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                }`}
              >
                {type}
                {type !== "All" && (
                  <span className="ml-2 text-xs">
                    ({checks.filter((c) => c.type === type).length})
                  </span>
                )}
              </button>
            ))}
          </div>

          <DataTable data={filteredChecks} columns={checksColumns} />
        </CardContent>
      </Card>

      {/* Quarantine Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            Quarantine Area
          </CardTitle>
          <CardDescription>
            Records that failed quality checks and require attention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable data={quarantined} columns={quarantineColumns} />
        </CardContent>
      </Card>
    </div>
  );
}
