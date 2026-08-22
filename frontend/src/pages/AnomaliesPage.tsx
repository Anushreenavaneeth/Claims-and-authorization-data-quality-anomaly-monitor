import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search, Filter, ChevronLeft, ChevronRight, AlertTriangle,
} from 'lucide-react';
import DashboardShell from '../components/DashboardShell';
import { getIntegratedAnomalies } from '../services/integratedApi';
import type { IntegratedRecord, PaginatedResponse } from '../types/integrated';

// ── Badge components ───────────────────────────────────────────────────────
const SEVERITY_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  CRITICAL: { bg: 'rgba(239,68,68,0.12)',  text: '#fca5a5', dot: '#ef4444' },
  HIGH:     { bg: 'rgba(249,115,22,0.12)', text: '#fdba74', dot: '#f97316' },
  MEDIUM:   { bg: 'rgba(234,179,8,0.12)',  text: '#fde047', dot: '#eab308' },
  LOW:      { bg: 'rgba(34,197,94,0.10)',  text: '#86efac', dot: '#22c55e' },
};

const SLA_STYLES: Record<string, { bg: string; text: string }> = {
  BREACHED: { bg: 'rgba(239,68,68,0.12)',  text: '#fca5a5' },
  AT_RISK:  { bg: 'rgba(249,115,22,0.12)', text: '#fdba74' },
  ELEVATED: { bg: 'rgba(234,179,8,0.12)',  text: '#fde047' },
  NORMAL:   { bg: 'rgba(34,197,94,0.10)',  text: '#86efac' },
};

const DATASET_STYLES: Record<string, { bg: string; text: string }> = {
  claims:        { bg: 'rgba(59,130,246,0.12)',  text: '#93c5fd' },
  authorization: { bg: 'rgba(167,139,250,0.12)', text: '#c4b5fd' },
  pharmacy:      { bg: 'rgba(52,211,153,0.12)',  text: '#6ee7b7' },
};

function Badge({ label, style }: { label: string; style?: { bg: string; text: string; dot?: string } }) {
  const s = style ?? { bg: 'rgba(100,116,139,0.15)', text: '#94a3b8' };
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium"
          style={{ background: s.bg, color: s.text }}>
      {s.dot && <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.dot }} />}
      {label}
    </span>
  );
}

// ── Table row ──────────────────────────────────────────────────────────────
function AnomalyRow({ record, onClick }: { record: IntegratedRecord; onClick: () => void }) {
  const sev = SEVERITY_STYLES[record.anomaly.severity] ?? SEVERITY_STYLES.LOW;
  const sla = SLA_STYLES[record.sla.status]            ?? SLA_STYLES.NORMAL;
  const ds  = DATASET_STYLES[record.dataset]           ?? { bg: 'rgba(100,116,139,0.1)', text: '#94a3b8' };

  return (
    <tr
      onClick={onClick}
      className="cursor-pointer border-b transition-colors"
      style={{ borderColor: 'rgba(255,255,255,0.04)' }}
      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.025)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      <td className="px-4 py-3">
        <p className="text-xs font-mono text-slate-200 truncate max-w-[160px]">{record.record_id}</p>
      </td>
      <td className="px-4 py-3">
        <Badge label={record.dataset} style={ds} />
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        <span className="text-xs font-mono text-slate-300">{record.anomaly.anomaly_score.toFixed(3)}</span>
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        <span className="text-xs font-mono text-slate-300">{record.quality.quality_score.toFixed(0)}</span>
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        <span className="text-xs font-mono text-slate-300">{record.sla.risk_score.toFixed(1)}</span>
      </td>
      <td className="px-4 py-3">
        <Badge label={record.anomaly.severity} style={sev} />
      </td>
      <td className="px-4 py-3">
        <p className="text-xs font-mono text-slate-400 truncate max-w-[180px]">
          {record.rules.rule_names[0]?.replace(/_/g, ' ') || record.bayesian.is_anomaly ? 'Bayesian flag' : '—'}
        </p>
      </td>
      <td className="px-4 py-3">
        <Badge label={record.sla.status} style={sla} />
      </td>
      <td className="px-4 py-3">
        <span className="text-[10px] font-mono px-2 py-1 rounded-full"
              style={{ background: 'rgba(59,130,246,0.1)', color: '#93c5fd' }}>
          {record.sla.priority}
        </span>
      </td>
    </tr>
  );
}

// ── Filter bar ─────────────────────────────────────────────────────────────
function FilterSelect({
  label, value, onChange, options,
}: {
  label: string; value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="text-xs font-mono rounded-lg px-3 py-1.5 outline-none appearance-none"
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#cbd5e1',
          minWidth: 120,
        }}
      >
        {options.map(o => (
          <option key={o.value} value={o.value}
                  style={{ background: '#0f172a', color: '#cbd5e1' }}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export default function AnomaliesPage() {
  const navigate      = useNavigate();
  const [searchParams] = useSearchParams();

  const [data,    setData]    = useState<PaginatedResponse<IntegratedRecord> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  // Filters
  const [dataset,    setDataset]    = useState(searchParams.get('dataset')    ?? '');
  const [severity,   setSeverity]   = useState(searchParams.get('severity')   ?? '');
  const [slaStatus,  setSlaStatus]  = useState(searchParams.get('sla_status') ?? '');
  const [isAnomaly,  setIsAnomaly]  = useState(searchParams.get('anomaly')    ?? '');
  const [search,     setSearch]     = useState('');
  const [page,       setPage]       = useState(1);
  const PAGE_SIZE = 50;

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);

    const params: Record<string, unknown> = { page, page_size: PAGE_SIZE };
    if (dataset)   params.dataset    = dataset;
    if (severity)  params.severity   = severity;
    if (slaStatus) params.sla_status = slaStatus;
    if (isAnomaly === 'yes') params.is_anomaly = true;
    if (isAnomaly === 'no')  params.is_anomaly = false;
    if (search)    params.search     = search;

    getIntegratedAnomalies(params as any)
      .then(setData)
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? 'Failed to load'))
      .finally(() => setLoading(false));
  }, [dataset, severity, slaStatus, isAnomaly, search, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Reset page on filter change
  const handleFilter = (setter: (v: string) => void) => (v: string) => {
    setter(v);
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <DashboardShell>
      {/* Header */}
      <div className="flex items-end justify-between mb-6">
        <div>
          <p className="text-[10px] font-mono tracking-[0.2em] text-slate-600 uppercase mb-1">Anomaly Monitor</p>
          <h1 className="text-2xl font-bold text-white">Anomaly Records</h1>
          {data && (
            <p className="text-sm text-slate-500 mt-1">
              {data.total.toLocaleString()} records
              {data.items.filter(r => r.anomaly.is_anomaly).length > 0 &&
                ` · ${data.items.filter(r => r.anomaly.is_anomaly).length} anomalies on this page`}
            </p>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-2xl p-4 mb-5"
           style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex flex-wrap items-end gap-4">
          {/* Search */}
          <div className="flex flex-col gap-1 flex-1 min-w-[200px]">
            <label className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">Search Record ID</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                placeholder="e.g. CLAIMS-10091..."
                className="w-full pl-8 pr-3 py-1.5 text-xs font-mono rounded-lg outline-none"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#cbd5e1' }}
              />
            </div>
          </div>

          <FilterSelect
            label="Dataset" value={dataset} onChange={handleFilter(setDataset)}
            options={[
              { value: '', label: 'All Datasets' },
              { value: 'claims', label: 'Claims' },
              { value: 'authorization', label: 'Authorization' },
              { value: 'pharmacy', label: 'Pharmacy' },
            ]}
          />

          <FilterSelect
            label="Severity" value={severity} onChange={handleFilter(setSeverity)}
            options={[
              { value: '', label: 'All Severities' },
              { value: 'CRITICAL', label: 'Critical' },
              { value: 'HIGH', label: 'High' },
              { value: 'MEDIUM', label: 'Medium' },
              { value: 'LOW', label: 'Low' },
            ]}
          />

          <FilterSelect
            label="SLA Status" value={slaStatus} onChange={handleFilter(setSlaStatus)}
            options={[
              { value: '', label: 'All SLA' },
              { value: 'BREACHED', label: 'Breached' },
              { value: 'AT_RISK', label: 'At Risk' },
              { value: 'ELEVATED', label: 'Elevated' },
              { value: 'NORMAL', label: 'Normal' },
            ]}
          />

          <FilterSelect
            label="Anomaly" value={isAnomaly} onChange={handleFilter(setIsAnomaly)}
            options={[
              { value: '', label: 'All Records' },
              { value: 'yes', label: 'Anomalies Only' },
              { value: 'no', label: 'Normal Only' },
            ]}
          />

          <button
            onClick={() => { setDataset(''); setSeverity(''); setSlaStatus(''); setIsAnomaly(''); setSearch(''); setPage(1); }}
            className="px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#64748b' }}
          >
            <Filter className="w-3 h-3" /> Clear
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm font-mono flex items-center gap-2"
             style={{ background: 'rgba(239,68,68,0.07)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
          <AlertTriangle className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Table */}
      <div className="rounded-2xl overflow-hidden"
           style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                {['Record ID', 'Dataset', 'Anomaly Score', 'Quality Score', 'Risk Score',
                  'Severity', 'Root Cause', 'SLA Status', 'Priority'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 rounded animate-pulse bg-slate-800/60" style={{ width: `${40 + Math.random() * 50}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-16 text-center text-slate-600 font-mono text-sm">
                    No records found. Try adjusting the filters.
                  </td>
                </tr>
              ) : (
                data?.items.map(record => (
                  <AnomalyRow
                    key={record.record_id}
                    record={record}
                    onClick={() => navigate(`/admin/anomalies/${encodeURIComponent(record.record_id)}`)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total > PAGE_SIZE && (
          <div className="flex items-center justify-between px-4 py-3"
               style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <p className="text-xs font-mono text-slate-500">
              {((page - 1) * PAGE_SIZE) + 1}–{Math.min(page * PAGE_SIZE, data.total)} of {data.total.toLocaleString()}
            </p>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1 || loading}
                onClick={() => setPage(p => p - 1)}
                className="p-1.5 rounded-lg transition-all disabled:opacity-30"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)' }}
              >
                <ChevronLeft className="w-3.5 h-3.5 text-slate-400" />
              </button>
              <span className="text-xs font-mono text-slate-400">
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages || loading}
                onClick={() => setPage(p => p + 1)}
                className="p-1.5 rounded-lg transition-all disabled:opacity-30"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)' }}
              >
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
