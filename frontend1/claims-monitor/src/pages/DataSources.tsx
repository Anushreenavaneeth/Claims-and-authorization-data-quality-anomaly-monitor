import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { getDataSources } from "../services/api";
import { formatNumber, formatDate } from "../lib/utils";
import { Database, RefreshCw } from "lucide-react";
import type { DataSource } from "../types";

export function DataSources() {
  const [sources, setSources] = useState<DataSource[]>([]);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    const data = await getDataSources();
    setSources(data);
  };

  const columns: Column<DataSource>[] = [
    {
      key: "name",
      label: "Source Name",
      sortable: true,
      render: (row) => (
        <div>
          <div className="font-medium">{row.name}</div>
          <div className="text-xs text-muted-foreground">{row.subType}</div>
        </div>
      ),
    },
    {
      key: "type",
      label: "Type",
      sortable: true,
    },
    {
      key: "recordCount",
      label: "Records",
      sortable: true,
      render: (row) => formatNumber(row.recordCount),
    },
    {
      key: "ingestionRate",
      label: "Ingestion Rate",
      sortable: true,
      render: (row) => `${row.ingestionRate || 0}/min`,
    },
    {
      key: "errorCount",
      label: "Errors",
      sortable: true,
      render: (row) => (
        <span className={row.errorCount > 50 ? "text-red-600 font-medium" : ""}>
          {row.errorCount}
        </span>
      ),
    },
    {
      key: "lastSync",
      label: "Last Sync",
      sortable: true,
      render: (row) => (
        <span className="text-xs">{formatDate(row.lastSync)}</span>
      ),
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Sources</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage data ingestion from all sources
          </p>
        </div>
        <button
          onClick={loadSources}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sources.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Healthy Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {sources.filter((s) => s.status === "healthy").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Records
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(sources.reduce((sum, s) => sum + s.recordCount, 0))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {sources.reduce((sum, s) => sum + s.errorCount, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sources Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Data Sources</CardTitle>
          <CardDescription>
            Detailed view of all connected data sources and their current status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={sources}
            columns={columns}
          />
        </CardContent>
      </Card>

      {/* Detailed Cards by Type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {["Claims", "Prescriber", "Pharmacy", "Authorization"].map((type) => {
          const typeSources = sources.filter((s) => s.type === type);
          if (typeSources.length === 0) return null;

          return (
            <Card key={type}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  {type} Data
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {typeSources.map((source) => (
                    <div
                      key={source.id}
                      className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold">{source.name}</h4>
                          <p className="text-xs text-muted-foreground">{source.subType}</p>
                        </div>
                        <StatusBadge status={source.status} />
                      </div>
                      
                      {source.description && (
                        <p className="text-sm text-muted-foreground mb-3">
                          {source.description}
                        </p>
                      )}

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <div className="text-muted-foreground text-xs">Records</div>
                          <div className="font-medium">{formatNumber(source.recordCount)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground text-xs">Errors</div>
                          <div className={`font-medium ${source.errorCount > 50 ? "text-red-600" : ""}`}>
                            {source.errorCount}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground text-xs">Ingestion Rate</div>
                          <div className="font-medium">{source.ingestionRate || 0}/min</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground text-xs">Last Sync</div>
                          <div className="font-medium text-xs">
                            {new Date(source.lastSync).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
