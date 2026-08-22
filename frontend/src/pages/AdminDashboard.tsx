import { useEffect, useState } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  XAxis, YAxis, Legend,
} from 'recharts';
import {
  ShieldAlert, AlertTriangle, Activity, CheckCircle2,
  TrendingUp, Clock, Database, Zap, RefreshCw,
} from 'lucide-react';
import DashboardShell from '../components/DashboardShell';
import { getDashboardSummary } from '../services/integratedApi';
import type { DashboardSummary } from '../types/integrated';
import { useNavigate } from 'react-router-dom';

// ── Colour palette ─────────────────────────────────────────────────────────
const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#22c55e',
};
const SLA_COLORS: Record<string, string> = {
  BREACHED: '#ef4444',
  AT_RISK:  '#f97316',
  ELEVATED: '#eab308',
  NORMAL:   '#22c55e',
};
const DATASET_COLORS = ['#3b82f6', '#a78bfa', '#34d399'];

// ── Stat card ──────────────────────────────────────────────────────────────
function StatCard({
  label, value, sub, color, icon: Icon, loading, onClick,
}: {
  label: string; value: string | number; sub: string;
  color: string; icon: React.ElementType;
  loading?: boolean; onClick?: () => void;
}) {
  return (
    <div
      className={`rounded-2xl p-5 transition-all duration-200 ${onClick ? 'cursor-pointer hover:-translate-y-0.5' : ''}`}
      style={{
        background: 'linear-gradient(135deg, rgba(6,14,28,0.95), rgba(10,20,40,0.85))',
        border: `1px solid ${color}30`,
        boxShadow: `0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px ${color}10`,
      }}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500">{label}</p>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      {loading ? (
        <div className="h-9 w-20 rounded-lg animate-pulse bg-slate-800 mb-1" />
      ) : (
        <p className="text-3xl font-bold text-white tabular-nums mb-1">{value}</p>
      )}
      <p className="text-[11px] font-mono text-slate-500">{sub}</p>
      <div className="h-px mt-4 rounded-full"
           style={{ background: `linear-gradient(90deg, transparent, ${color}50, transparent)` }} />
    </div>
  );
}

// ── Quality meter ──────────────────────────────────────────────────────────
function QualityMeter({ score }: { score: number }) {
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444';
  const angle = (score / 100) * 180;
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-16 overflow-hidden">
        <div className="absolute inset-0 rounded-t-full border-8"
             style={{ borderColor: 'rgba(255,255,255,0.06)', borderBottom: 'none' }} />
        <div className="absolute inset-0 rounded-t-full border-8 transition-all duration-700"
             style={{
               borderColor: `transparent transparent ${color} ${color}`,
               borderBottom: 'none',
               transform: `rotate(${angle - 180}deg)`,
               transformOrigin: '50% 100%',
             }} />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <p className="text-2xl font-bold text-white tabular-nums leading-none">{score.toFixed(0)}</p>
          <p className="text-[9px] text-slate-500 font-mono">/100</p>
        </div>
      </div>
    </div>
  );
}

// ── Dataset bar ────────────────────────────────────────────────────────────
function DatasetBar({ name, total, anomalies, color }: { name: string; total: number; anomalies: number; color: string }) {
  const pct = total > 0 ? (anomalies / total) * 100 : 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-mono text-slate-300 capitalize">{name}</span>
        <span className="text-xs font-mono text-slate-500">{anomalies} / {total}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800/60 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <p className="text-[10px] font-mono text-slate-600 mt-0.5">{pct.toFixed(1)}% anomaly rate</p>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export default function AdminDashboard() {
  const navigate  = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDashboardSummary()
      .then(s => { setSummary(s); })
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? 'Failed to load dashboard data'))
      .finally(() => setLoading(false));
  }, [refresh]);

  // ── Derived chart data ───────────────────────────────────────────────────
  const severityData = summary
    ? Object.entries(summary.severity_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const slaData = summary
    ? Object.entries(summary.sla_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  const datasetBarData = (summary?.datasets ?? []).map((d, i) => ({
    name:      d.dataset,
    total:     d.total,
    anomalies: d.anomalies,
    normal:    d.total - d.anomalies,
    color:     DATASET_COLORS[i % DATASET_COLORS.length],
  }));

  return (
    <DashboardShell>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-end justify-between mb-8">
        <div>
          <p className="text-[10px] font-mono tracking-[0.2em] text-slate-600 uppercase mb-1">
            Healthcare · Data Quality Monitor
          </p>
          <h1 className="text-3xl font-bold text-white">Platform Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time anomaly detection across Claims, Authorization &amp; Pharmacy
          </p>
        </div>
        <button
          onClick={() => setRefresh(r => r + 1)}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-mono transition-all"
          style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa' }}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* ── Error banner ───────────────────────────────────────────────── */}
      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl text-sm font-mono flex items-center gap-3"
             style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error} — Run the pipeline first via POST /api/process
        </div>
      )}

      {/* ── KPI stat cards ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Records"     value={summary?.total_records ?? 0}    sub="across all datasets"      color="#60a5fa" icon={Database}    loading={loading} />
        <StatCard label="Total Anomalies"   value={summary?.total_anomalies ?? 0}  sub={`${summary?.anomaly_rate ?? 0}% anomaly rate`} color="#f87171" icon={ShieldAlert} loading={loading} onClick={() => navigate('/admin/anomalies')} />
        <StatCard label="SLA Breaches"      value={summary?.sla_breaches ?? 0}     sub="immediate action required" color="#ef4444"  icon={Clock}      loading={loading} />
        <StatCard label="Avg Quality Score" value={`${summary?.average_quality_score ?? 0}%`} sub="data quality index" color="#34d399" icon={CheckCircle2} loading={loading} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Critical Issues"   value={summary?.critical_issues ?? 0} sub="P1 — 1 hour SLA"    color="#ef4444" icon={AlertTriangle} loading={loading} />
        <StatCard label="High Issues"       value={summary?.high_issues ?? 0}     sub="P2 — 4 hour SLA"    color="#f97316" icon={TrendingUp}    loading={loading} />
        <StatCard label="Medium Issues"     value={summary?.medium_issues ?? 0}   sub="P3 — 24 hour SLA"   color="#eab308" icon={Activity}      loading={loading} />
        <StatCard label="SLA At Risk"       value={summary?.sla_at_risk ?? 0}     sub="approaching breach" color="#f97316" icon={Zap}           loading={loading} />
      </div>

      {/* ── Charts row ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">

        {/* Severity distribution */}
        <div className="rounded-2xl p-5"
             style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">Severity Distribution</p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                     paddingAngle={3} dataKey="value">
                  {severityData.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? '#64748b'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#94a3b8' }} itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend iconType="circle" iconSize={8}
                  formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* SLA status */}
        <div className="rounded-2xl p-5"
             style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">SLA Status</p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={slaData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                     paddingAngle={3} dataKey="value">
                  {slaData.map((entry) => (
                    <Cell key={entry.name} fill={SLA_COLORS[entry.name] ?? '#64748b'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#94a3b8' }} itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend iconType="circle" iconSize={8}
                  formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Quality score */}
        <div className="rounded-2xl p-5 flex flex-col items-center justify-center"
             style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">Avg Quality Score</p>
          {loading ? (
            <div className="h-20 w-20 rounded-full animate-pulse bg-slate-800" />
          ) : (
            <QualityMeter score={summary?.average_quality_score ?? 0} />
          )}
          <p className="text-xs text-slate-500 font-mono mt-3 text-center">
            {(summary?.normal_records ?? 0).toLocaleString()} records passing all checks
          </p>
        </div>
      </div>

      {/* ── Dataset comparison ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">

        {/* Stacked bar */}
        <div className="rounded-2xl p-5"
             style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">Anomalies by Dataset</p>
          {loading ? (
            <div className="h-40 flex items-center justify-center text-slate-600 text-sm">Loading…</div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={datasetBarData} barCategoryGap="30%">
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Legend iconType="square" iconSize={8}
                  formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>} />
                <Bar dataKey="anomalies" name="Anomalies" stackId="a" fill="#ef4444" radius={[0,0,0,0]} />
                <Bar dataKey="normal"    name="Normal"    stackId="a" fill="#1e3a5f" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Dataset progress bars */}
        <div className="rounded-2xl p-5"
             style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">Dataset Anomaly Rates</p>
          {loading ? (
            <div className="space-y-3">
              {[0,1,2].map(i => <div key={i} className="h-10 rounded-lg animate-pulse bg-slate-800" />)}
            </div>
          ) : (
            <div className="pt-1">
              {datasetBarData.map((d) => (
                <DatasetBar key={d.name} name={d.name} total={d.total}
                            anomalies={d.anomalies} color={d.color} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Quick actions ──────────────────────────────────────────────── */}
      <div className="rounded-2xl p-5"
           style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <p className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">Quick Actions</p>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/admin/anomalies')}
            className="px-4 py-2 rounded-xl text-sm font-mono transition-all"
            style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)', color: '#60a5fa' }}
          >
            View All Anomalies →
          </button>
          <button
            onClick={() => navigate('/admin/anomalies?sla_status=BREACHED')}
            className="px-4 py-2 rounded-xl text-sm font-mono transition-all"
            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}
          >
            SLA Breaches ({summary?.sla_breaches ?? 0}) →
          </button>
          <button
            onClick={() => navigate('/admin/anomalies?severity=HIGH')}
            className="px-4 py-2 rounded-xl text-sm font-mono transition-all"
            style={{ background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.2)', color: '#fb923c' }}
          >
            High Risk ({summary?.high_issues ?? 0}) →
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}
