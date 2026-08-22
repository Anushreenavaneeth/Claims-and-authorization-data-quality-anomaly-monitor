import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import api from "../services/api";
import {
  Upload, FileText, CheckCircle2, AlertCircle,
  Loader2, ChevronDown, ChevronUp, Database, RefreshCw,
} from "lucide-react";

type SourceType = "CLAIMS" | "PHARMACY" | "AUTHORIZATION";
type UploadStatus = "idle" | "uploading" | "success" | "error";

interface Issue {
  type: string;
  severity: string;
  column?: string;
  rows?: number;
  message: string;
}

interface UploadResult {
  upload_id:         string;
  filename:          string;
  source_type:       string;
  total_records:     number;
  valid_records:     number;
  invalid_records:   number;
  status:            string;
  issues:            Issue[];
  anomalies_created: number;
  timestamp:         string;
}

const SOURCE_OPTIONS: { value: SourceType; label: string; desc: string }[] = [
  { value: "CLAIMS",        label: "Claims",        desc: "Insurance claims data" },
  { value: "PHARMACY",      label: "Pharmacy",      desc: "Prescription / drug data" },
  { value: "AUTHORIZATION", label: "Authorization", desc: "Pre-auth / approval records" },
];

export default function DataSources() {
  const [sourceType, setSourceType] = useState<SourceType>("CLAIMS");
  const [status,     setStatus]     = useState<UploadStatus>("idle");
  const [result,     setResult]     = useState<UploadResult | null>(null);
  const [errorMsg,   setErrorMsg]   = useState("");
  const [showIssues, setShowIssues] = useState(false);
  const [dragOver,   setDragOver]   = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = async (file: File) => {
    setStatus("uploading");
    setResult(null);
    setErrorMsg("");

    const form = new FormData();
    form.append("file", file);
    form.append("source_type", sourceType);

    try {
      const res = await api.post("/datasets/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      setStatus("success");
      setShowIssues(res.data.issues.length > 0);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setErrorMsg(typeof detail === "string" ? detail : "Upload failed. Try again.");
      setStatus("error");
    }
  };

  const handleFile = (file: File | null) => {
    if (!file) return;
    if (!file.name.endsWith(".csv")) {
      setErrorMsg("Only .csv files are supported.");
      setStatus("error");
      return;
    }
    upload(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0] ?? null);
  };

  const reset = () => {
    setStatus("idle");
    setResult(null);
    setErrorMsg("");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold">Data Sources</h1>
        <p className="text-muted-foreground mt-1">
          Upload and validate Claims, Pharmacy, or Authorization datasets
        </p>
      </div>

      <div className="max-w-2xl space-y-5">

        {/* Dataset type selector */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Select Dataset Type</CardTitle>
            <CardDescription>Choose the type of data you are uploading</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3">
              {SOURCE_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => { setSourceType(opt.value); reset(); }}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    sourceType === opt.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/30"
                  }`}
                >
                  <p className={`text-sm font-semibold ${sourceType === opt.value ? "text-blue-700" : "text-gray-900"}`}>
                    {opt.label}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Drop zone */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Upload File</CardTitle>
            <CardDescription>
              {sourceType} · CSV only · validated against schema
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => status !== "uploading" && inputRef.current?.click()}
              className={`rounded-lg border-2 border-dashed cursor-pointer transition-all p-10 flex flex-col items-center gap-3 text-center ${
                dragOver
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/30"
              } ${status === "uploading" ? "cursor-default" : ""}`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={e => handleFile(e.target.files?.[0] ?? null)}
              />

              {status === "uploading" ? (
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
              ) : (
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <Upload className="w-6 h-6 text-blue-600" />
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-700">
                  {status === "uploading"
                    ? "Validating and processing…"
                    : "Drop your CSV file here or click to browse"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Supports: .csv — max 50 MB
                </p>
              </div>
            </div>

            {/* Error message */}
            {status === "error" && (
              <div className="mt-4 flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                {errorMsg}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Result card */}
        {status === "success" && result && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <CardTitle className="text-base">{result.filename}</CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {result.source_type} · {result.timestamp.slice(0, 19).replace("T", " ")} UTC
                    </p>
                  </div>
                </div>
                <Badge variant={result.status === "PASS" ? "success" : "error"}>
                  {result.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">

              {/* Stats row */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: "Total Records", value: result.total_records, variant: "default" as const },
                  { label: "Valid",         value: result.valid_records,   variant: "success" as const },
                  { label: "Invalid",       value: result.invalid_records, variant: result.invalid_records > 0 ? "error" as const : "success" as const },
                  { label: "Anomalies",     value: result.anomalies_created, variant: result.anomalies_created > 0 ? "warning" as const : "default" as const },
                ].map(s => (
                  <div key={s.label} className="text-center p-3 bg-gray-50 rounded-lg border">
                    <p className="text-2xl font-bold">{s.value}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Anomaly banner */}
              {result.anomalies_created > 0 && (
                <div className="flex items-center gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg text-sm">
                  <CheckCircle2 className="w-4 h-4 text-orange-600 flex-shrink-0" />
                  <span className="text-orange-700">
                    {result.anomalies_created} anomaly record{result.anomalies_created > 1 ? "s" : ""} detected and saved.
                  </span>
                </div>
              )}

              {/* Issues accordion */}
              {result.issues.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowIssues(s => !s)}
                    className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-500" />
                      {result.issues.length} validation issue{result.issues.length > 1 ? "s" : ""} found
                    </span>
                    {showIssues ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  {showIssues && (
                    <div className="divide-y">
                      {result.issues.map((iss, i) => (
                        <div key={i} className="flex items-start gap-3 px-4 py-3 text-sm">
                          <Badge variant={iss.severity === "ERROR" ? "error" : "warning"} className="flex-shrink-0 mt-0.5">
                            {iss.severity}
                          </Badge>
                          <span className="text-muted-foreground">
                            {iss.column && <span className="text-blue-600 font-medium">{iss.column}: </span>}
                            {iss.message}
                            {iss.rows != null && <span className="text-gray-400"> ({iss.rows} rows)</span>}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Upload another */}
              <button
                onClick={reset}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Upload another file
              </button>
            </CardContent>
          </Card>
        )}

        {/* Info card */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Database className="w-4 h-4" /> Supported Formats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>• <strong>Claims</strong> — validates schema, required fields, data types</p>
              <p>• <strong>Pharmacy</strong> — validates schema, NDC codes, required fields</p>
              <p>• <strong>Authorization</strong> — validates schema + runs ML anomaly detection</p>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
