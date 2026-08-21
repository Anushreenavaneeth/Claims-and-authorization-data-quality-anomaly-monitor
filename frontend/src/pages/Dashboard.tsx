import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  AlertTriangle, CheckCircle, Clock, Database, Upload,
  LogOut, ShieldCheck, Activity, FileText, RefreshCw,
  TrendingUp, Zap, X
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────
interface AnomalySummary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

interface UploadResult {
  upload_id: string;
  filename: string;
  source_type: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  status: string;
  anomalies_created: number;
  issues: { column?: string; message: string }[];
}

// ── API helper ─────────────────────────────────────────────────────
const API = "http://localhost:8000";

function useApi(token: string | null) {
  const get = useCallback(
    async (path: string) => {
      const res = await fetch(`${API}${path}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    },
    [token]
  );
  return { get };
}

// ── Stat Card ──────────────────────────────────────────────────────
function StatCard({
  icon: Icon, label, value, color, subtext,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  color: string;
  subtext?: string;
}) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-3 transition-all hover:scale-[1.02]"
      style={{
        background: "rgba(6,14,28,0.7)",
        border: "1px solid rgba(96,165,250,0.12)",
        boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono tracking-widest uppercase text-slate-500">{label}</span>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: color + "22", border: `1px solid ${color}44` }}
        >
          <Icon size={14} style={{ color }} />
        </div>
      </div>
      <div>
        <span className="text-3xl font-bold text-white font-display">{value}</span>
        {subtext && <p className="text-[10px] font-mono text-slate-600 mt-1">{subtext}</p>}
      </div>
    </div>
  );
}

// ── Upload Panel ───────────────────────────────────────────────────
function UploadPanel({ token, onDone }: { token: string | null; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState("CLAIMS");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");
  const dropRef = useRef<HTMLDivElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith(".csv")) setFile(f);
    else setError("Only CSV files accepted.");
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("source_type", sourceType);
      const res = await fetch(`${API}/datasets/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || "Upload failed");
      }
      const data = await res.json();
      setResult(data);
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="rounded-xl p-6"
      style={{
        background: "rgba(6,14,28,0.7)",
        border: "1px solid rgba(96,165,250,0.12)",
        backdropFilter: "blur(12px)",
      }}
    >
      <h2 className="text-sm font-mono font-bold text-white mb-5 flex items-center gap-2">
        <Upload size={14} className="text-blue-400" /> Upload Dataset
      </h2>

      {/* Source type selector */}
      <div className="flex gap-2 mb-4">
        {["CLAIMS", "PHARMACY", "AUTHORIZATION"].map((t) => (
          <button
            key={t}
            onClick={() => setSourceType(t)}
            className="flex-1 py-1.5 rounded-lg text-[10px] font-mono tracking-widest uppercase transition-all"
            style={{
              background: sourceType === t ? "rgba(37,99,235,0.3)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${sourceType === t ? "rgba(96,165,250,0.5)" : "rgba(96,165,250,0.1)"}`,
              color: sourceType === t ? "#93c5fd" : "#475569",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Drop zone */}
      <div
        ref={dropRef}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => document.getElementById("file-input")?.click()}
        className="rounded-lg border-2 border-dashed flex flex-col items-center justify-center py-8 cursor-pointer transition-all mb-4"
        style={{
          borderColor: file ? "rgba(52,211,153,0.4)" : "rgba(96,165,250,0.2)",
          background: file ? "rgba(52,211,153,0.04)" : "rgba(96,165,250,0.02)",
        }}
      >
        <input
          id="file-input"
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setFile(f);
          }}
        />
        {file ? (
          <div className="text-center">
            <FileText size={20} className="mx-auto mb-2 text-emerald-400" />
            <p className="text-xs font-mono text-emerald-400">{file.name}</p>
            <p className="text-[10px] font-mono text-slate-600 mt-1">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
        ) : (
          <div className="text-center">
            <Upload size={20} className="mx-auto mb-2 text-slate-600" />
            <p className="text-xs font-mono text-slate-500">Drop CSV here or click to browse</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-3 px-3 py-2 rounded-lg text-xs font-mono text-red-400"
          style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)" }}>
          ✗ {error}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className="w-full py-2.5 rounded-lg text-xs font-mono font-bold text-white transition-all disabled:opacity-40 flex items-center justify-center gap-2"
        style={{
          background: "linear-gradient(135deg, rgba(37,99,235,0.9), rgba(14,116,144,0.8))",
          border: "1px solid rgba(96,165,250,0.3)",
        }}
      >
        {loading ? (
          <><RefreshCw size={12} className="animate-spin" /> processing…</>
        ) : (
          <><Zap size={12} /> validate & ingest</>
        )}
      </button>

      {/* Result */}
      {result && (
        <div className="mt-4 p-4 rounded-lg" style={{
          background: result.status === "PASS" ? "rgba(52,211,153,0.06)" : "rgba(239,68,68,0.06)",
          border: `1px solid ${result.status === "PASS" ? "rgba(52,211,153,0.2)" : "rgba(239,68,68,0.2)"}`,
        }}>
          <div className="flex items-center gap-2 mb-2">
            {result.status === "PASS"
              ? <CheckCircle size={12} className="text-emerald-400" />
              : <AlertTriangle size={12} className="text-red-400" />}
            <span className="text-[10px] font-mono font-bold"
              style={{ color: result.status === "PASS" ? "#34d399" : "#f87171" }}>
              {result.status} — {result.filename}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Total", result.total_records],
              ["Valid", result.valid_records],
              ["Invalid", result.invalid_records],
            ].map(([k, v]) => (
              <div key={String(k)} className="text-center">
                <p className="text-lg font-bold text-white font-display">{v}</p>
                <p className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">{k}</p>
              </div>
            ))}
          </div>
          {result.anomalies_created > 0 && (
            <p className="mt-2 text-[10px] font-mono text-amber-400">
              ⚠ {result.anomalies_created} anomalies flagged
            </p>
          )}
          {result.issues.length > 0 && (
            <div className="mt-2 max-h-24 overflow-y-auto">
              {result.issues.slice(0, 5).map((iss, i) => (
                <p key={i} className="text-[9px] font-mono text-slate-500 truncate">
                  • {iss.column ? `[${iss.column}] ` : ""}{iss.message}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────
export default function Dashboard() {
  const { user, token, logout } = useAuth();
  const { get } = useApi(token);
  const [summary, setSummary] = useState<AnomalySummary | null>(null);
  const [mlStatus, setMlStatus] = useState<{ available: boolean; error?: string } | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [time, setTime] = useState(new Date());
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [recentAlert, setRecentAlert] = useState<string | null>(null);

  // Clock
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Fetch summary and ML status
  useEffect(() => {
    // Try to get anomaly stats
    get("/protected/stats")
      .then((d) => setSummary(d))
      .catch(() => {
        // endpoint may not exist yet — show zeros
        setSummary({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
      });

    // Try ML health
    get("/ml/status")
      .then((d) => setMlStatus(d))
      .catch(() => setMlStatus({ available: false, error: "ML endpoint not available" }));
  }, [get, refreshKey]);

  // WebSocket for real-time anomaly alerts
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/telemetry");
    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("disconnected");
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "anomaly") {
          setRecentAlert(`New anomaly: ${data.data?.record_id ?? "unknown"}`);
          setTimeout(() => setRecentAlert(null), 5000);
          setRefreshKey((k) => k + 1);
        }
      } catch { /* ignore */ }
    };
    return () => ws.close();
  }, []);

  const stats = summary ?? { total: 0, critical: 0, high: 0, medium: 0, low: 0 };

  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(135deg, #06080f 0%, #030612 50%, #04080f 100%)" }}
    >
      {/* Top bar */}
      <header
        className="flex items-center justify-between px-6 py-4"
        style={{ borderBottom: "1px solid rgba(96,165,250,0.08)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(37,99,235,0.25)", border: "1px solid rgba(96,165,250,0.3)" }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h4M8 3v10M13 8H9" stroke="#60a5fa" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-bold text-white font-display leading-none">Claims Monitor</p>
            <p className="text-[9px] font-mono text-blue-400/50 tracking-widest uppercase mt-0.5">
              Healthcare Data Ops
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* WS status */}
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${wsStatus === "connected" ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`}
            />
            <span className="text-[9px] font-mono text-slate-600">
              {wsStatus === "connected" ? "live" : wsStatus}
            </span>
          </div>

          {/* Clock */}
          <span className="text-[10px] font-mono text-slate-600 hidden sm:block">
            {time.toLocaleTimeString()}
          </span>

          {/* User */}
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
              style={{ background: "rgba(37,99,235,0.4)", border: "1px solid rgba(96,165,250,0.3)" }}
            >
              {user?.name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-mono text-slate-300 leading-none">{user?.name ?? "User"}</p>
              <p className="text-[9px] font-mono text-slate-600 capitalize">{user?.role}</p>
            </div>
          </div>

          <button
            onClick={logout}
            title="Logout"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-mono text-slate-400 hover:text-red-400 transition-all"
            style={{ border: "1px solid rgba(96,165,250,0.1)" }}
          >
            <LogOut size={12} /> logout
          </button>
        </div>
      </header>

      {/* Real-time alert banner */}
      {recentAlert && (
        <div className="mx-6 mt-3 px-4 py-2 rounded-lg flex items-center justify-between"
          style={{ background: "rgba(234,179,8,0.1)", border: "1px solid rgba(234,179,8,0.3)" }}>
          <span className="text-xs font-mono text-yellow-400 flex items-center gap-2">
            <Activity size={12} /> {recentAlert}
          </span>
          <button onClick={() => setRecentAlert(null)}>
            <X size={12} className="text-slate-600 hover:text-slate-300" />
          </button>
        </div>
      )}

      <main className="p-6 max-w-7xl mx-auto">
        {/* Heading */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white font-display">
              Anomaly Dashboard
            </h1>
            <p className="text-xs font-mono text-slate-600 mt-1">
              Real-time data quality monitoring · Claims · Pharmacy · Authorization
            </p>
          </div>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-mono text-slate-400 hover:text-blue-400 transition-all"
            style={{ border: "1px solid rgba(96,165,250,0.12)" }}
          >
            <RefreshCw size={11} /> refresh
          </button>
        </div>

        {/* Stat grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard icon={AlertTriangle} label="Total Anomalies" value={stats.total}
            color="#f59e0b" subtext="All time" />
          <StatCard icon={Zap} label="Critical" value={stats.critical}
            color="#ef4444" subtext="Needs immediate review" />
          <StatCard icon={Clock} label="High" value={stats.high}
            color="#f97316" subtext="Review within 24h" />
          <StatCard icon={CheckCircle} label="Resolved" value={stats.low}
            color="#34d399" subtext="Low severity" />
        </div>

        {/* ML status + Upload */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* ML Status card */}
          <div
            className="rounded-xl p-5 flex flex-col gap-4"
            style={{
              background: "rgba(6,14,28,0.7)",
              border: "1px solid rgba(96,165,250,0.12)",
              backdropFilter: "blur(12px)",
            }}
          >
            <h2 className="text-sm font-mono font-bold text-white flex items-center gap-2">
              <ShieldCheck size={14} className="text-blue-400" /> ML Engine Status
            </h2>
            <div className="flex flex-col gap-3">
              {[
                { label: "Authorization", model: "IsolationForest v1" },
                { label: "Claims", model: "Rule Engine" },
                { label: "Pharmacy", model: "Rule Engine" },
              ].map((m) => (
                <div key={m.label} className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-mono text-slate-300">{m.label}</p>
                    <p className="text-[9px] font-mono text-slate-600">{m.model}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{
                        background: mlStatus === null
                          ? "#64748b"
                          : m.label === "Authorization" && mlStatus.available
                          ? "#34d399"
                          : "#f59e0b",
                      }}
                    />
                    <span className="text-[9px] font-mono text-slate-600">
                      {mlStatus === null ? "checking…"
                        : m.label === "Authorization" && mlStatus.available ? "online"
                        : "ready"}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pipeline visualization */}
            <div className="mt-2 pt-3" style={{ borderTop: "1px solid rgba(96,165,250,0.06)" }}>
              <p className="text-[9px] font-mono text-slate-700 uppercase tracking-widest mb-2">Pipeline</p>
              <div className="flex items-center gap-1.5 text-[9px] font-mono">
                {["Ingest", "Validate", "Score", "Alert"].map((step, i) => (
                  <div key={step} className="flex items-center gap-1.5">
                    <span
                      className="px-1.5 py-0.5 rounded pipeline-node-active"
                      style={{
                        background: "rgba(37,99,235,0.15)",
                        border: "1px solid rgba(96,165,250,0.2)",
                        color: "#93c5fd",
                        animationDelay: `${i * 0.5}s`,
                      }}
                    >{step}</span>
                    {i < 3 && (
                      <svg width="12" height="4" viewBox="0 0 12 4">
                        <line x1="0" y1="2" x2="12" y2="2"
                          stroke="rgba(96,165,250,0.3)" strokeWidth="1"
                          strokeDasharray="3 2" className="data-flow-line"
                          style={{ animationDelay: `${i * 0.3}s` }} />
                      </svg>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Upload Panel (spans 2 cols) */}
          <div className="md:col-span-2">
            <UploadPanel token={token} onDone={() => setRefreshKey((k) => k + 1)} />
          </div>
        </div>

        {/* Recent activity placeholder */}
        <div className="mt-4 rounded-xl p-5"
          style={{
            background: "rgba(6,14,28,0.5)",
            border: "1px solid rgba(96,165,250,0.08)",
            backdropFilter: "blur(8px)",
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-mono font-bold text-white flex items-center gap-2">
              <TrendingUp size={14} className="text-blue-400" /> Recent Uploads
            </h2>
            <Database size={12} className="text-slate-700" />
          </div>
          <p className="text-xs font-mono text-slate-700 text-center py-4">
            Upload a dataset above to see activity here.
          </p>
        </div>
      </main>
    </div>
  );
}
