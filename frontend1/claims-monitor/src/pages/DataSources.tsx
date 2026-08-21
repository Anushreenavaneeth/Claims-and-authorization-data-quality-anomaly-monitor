import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Badge } from "../components/ui/Badge";
import { getDataSources, uploadDatasetFile } from "../services/api";
import { formatNumber, formatDate } from "../lib/utils";
import { Database, RefreshCw, Upload, FileText, AlertCircle, Loader2, Cpu, ArrowRight } from "lucide-react";
import type { DataSource, DatasetUploadResult } from "../types";

export function DataSources() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<DataSource[]>([]);
  const [sourceType, setSourceType] = useState<"CLAIMS" | "PHARMACY" | "AUTHORIZATION">("AUTHORIZATION");
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadResult, setUploadResult] = useState<DatasetUploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);


  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    const data = await getDataSources();
    setSources(data);
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setUploadError("Only .csv files are supported.");
      setUploadStatus("error");
      return;
    }

    setUploadStatus("uploading");
    setUploadError(null);
    setUploadResult(null);

    try {
      const res = await uploadDatasetFile(file, sourceType);
      setUploadResult(res);
      setUploadStatus("success");
      loadSources();
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Upload failed. Verify backend service is running.";
      setUploadError(typeof msg === "string" ? msg : JSON.stringify(msg));
      setUploadStatus("error");
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
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
          <h1 className="text-3xl font-bold">Data Sources & Ingestion</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage data ingestion with automated ETL validation & ML anomaly detection
          </p>
        </div>
        <button
          onClick={loadSources}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 shadow-sm"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Dataset Ingestion Dropzone Card */}
      <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
        <CardHeader className="pb-3 border-b border-slate-100">
          <CardTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Upload className="h-4 w-4 text-blue-600" />
            Upload Dataset for Automated Pipeline & ML Scoring
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Upload CSV files for Claims, Pharmacy, or Authorization records. Authorization files are scored against the Isolation Forest model in real time.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-700">Target Schema:</span>
            {(["AUTHORIZATION", "CLAIMS", "PHARMACY"] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setSourceType(type)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-all ${
                  sourceType === type
                    ? "bg-blue-50 border-blue-300 text-blue-700 shadow-sm"
                    : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
                }`}
              >
                {type}
              </button>
            ))}
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? "border-blue-500 bg-blue-50/50"
                : "border-slate-200 hover:border-slate-300 bg-slate-50/50"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileUpload(e.target.files[0]);
                }
              }}
            />
            <div className="flex flex-col items-center gap-2">
              {uploadStatus === "uploading" ? (
                <>
                  <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
                  <p className="text-sm font-semibold text-slate-700">Validating schema & scoring ML models...</p>
                </>
              ) : (
                <>
                  <div className="p-3 bg-white rounded-full border border-slate-200 shadow-sm text-blue-600">
                    <Upload className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-800">
                    Drop CSV here or click to browse
                  </p>
                  <p className="text-xs text-slate-500 font-mono">
                    {sourceType} Pipeline · Validated against JSON schema rules
                  </p>
                </>
              )}
            </div>
          </div>

          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadResult && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-slate-600" />
                  <span className="font-semibold text-sm text-slate-900">{uploadResult.filename}</span>
                  <Badge variant={uploadResult.status === "PASS" ? "success" : "warning"}>
                    {uploadResult.status}
                  </Badge>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  Upload ID: {uploadResult.upload_id}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2 text-center">
                <div className="p-2 bg-white rounded-lg border border-slate-200">
                  <p className="text-xs text-slate-500">Total Rows</p>
                  <p className="text-base font-bold text-slate-800">{uploadResult.total_records}</p>
                </div>
                <div className="p-2 bg-white rounded-lg border border-slate-200">
                  <p className="text-xs text-slate-500">Valid Rows</p>
                  <p className="text-base font-bold text-emerald-600">{uploadResult.valid_records}</p>
                </div>
                <div className="p-2 bg-white rounded-lg border border-slate-200">
                  <p className="text-xs text-slate-500">Invalid Rows</p>
                  <p className="text-base font-bold text-rose-600">{uploadResult.invalid_records}</p>
                </div>
                <div className="p-2 bg-white rounded-lg border border-slate-200">
                  <p className="text-xs text-slate-500">Anomalies Stored</p>
                  <p className="text-base font-bold text-orange-600">{uploadResult.anomalies_created}</p>
                </div>
              </div>

              {/* Action Buttons with Analyse */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-200">
                <div className="text-xs text-slate-500">
                  Dataset ingested. Click <strong className="text-slate-800">Analyse</strong> to inspect ML outlier probabilities and root-cause deviations.
                </div>
                <div className="flex items-center gap-2.5 w-full sm:w-auto">
                  <button
                    type="button"
                    onClick={() => navigate('/anomalies')}
                    className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-xs transition-all"
                  >
                    <span>View Anomalies</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/ml-engine')}
                    className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-xs font-semibold text-white shadow-sm transition-all hover:bg-blue-700 active:scale-[0.99]"
                    style={{ background: '#2563eb' }}
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Analyse</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

        </CardContent>
      </Card>

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
