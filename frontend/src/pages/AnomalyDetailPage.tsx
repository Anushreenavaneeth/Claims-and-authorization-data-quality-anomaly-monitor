import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, ShieldAlert, BarChart2,
  Clock, CheckCircle2, XCircle, ChevronRight, Lightbulb,
  Activity, Database,
} from 'lucide-react';
import DashboardShell from '../components/DashboardShell';
import { getIntegratedAnomaly } from '../services/integratedApi';
import type { IntegratedRecord } from '../types/integrated';

// ── Palette helpers ────────────────────────────────────────────────────────
const SEV_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#eab308', LOW: '#22c55e',
};
const SLA_COLOR: Record<string, string> = {
  BREACHED: '#ef4444', AT_RISK: '#f97316', ELEVATED: '#eab308', NORMAL: '#22c55e',
};
const DS_COLOR: Record<string, string> = {
  claims: '#3b82f6', authorization: '#a78bfa', pharmacy: '#34d399',
};

// ── Sub-components ─────────────────────────────────────────────────────────

function SectionCard({ title, icon: Icon, color, children }: {
  title: string; icon: React.ElementType; color: string; children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl p-5"
         style={{ background: 'rgba(6,14,28,0.9)', border: `1px solid ${color}20` }}>
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Field({ label, value, mono = true, color }: {
  label: string; value: React.ReactNode; mono?: boolean; color?: string;
}) {
  return (
    <div className="mb-3">
      <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-0.5">{label}</p>
      <p className={`text-sm ${mono ? 'font-mono' : 'font-sans'} leading-relaxed`}
         style={{ color: color ?? '#cbd5e1' }}>
        {value || '—'}
      </p>
    </div>
  );
}

function ScoreBar({ label, value, max = 100, color }: {
  label: string; value: number; max?: number; color: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="mb-2">
      <div className="flex justify-between mb-1">
        <span className="text-[10px] font-mono text-slate-500">{label}</span>
        <span className="text-[10px] font-mono text-slate-300 tabular-nums">
          {value.toFixed(max > 1 ? 1 : 3)}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-800/60 overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700"
             style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium"
          style={{ background: `${color}15`, color, border: `1px solid ${color}25` }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}

function BulletList({ items, color = '#94a3b8' }: { items: string[]; color?: string }) {
  if (!items.length) return <p className="text-sm text-slate-600 font-mono">None</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2">
          <ChevronRight className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" style={{ color }} />
          <span className="text-xs font-mono leading-relaxed" style={{ color: '#94a3b8' }}>{item}</span>
        </li>
      ))}
    </ul>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export default function AnomalyDetailPage() {
  const { recordId }  = useParams<{ recordId: string }>();
  const navigate      = useNavigate();
  const [record, setRecord] = useState<IntegratedRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!recordId) return;
    setLoading(true);
    getIntegratedAnomaly(decodeURIComponent(recordId))
      .then(setRecord)
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? 'Failed to load'))
      .finally(() => setLoading(false));
  }, [recordId]);

  if (loading) {
    return (
      <DashboardShell>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
        </div>
      </DashboardShell>
    );
  }

  if (error || !record) {
    return (
      <DashboardShell>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <XCircle className="w-12 h-12 text-red-400" />
          <p className="text-slate-400 font-mono">{error ?? 'Record not found'}</p>
          <button onClick={() => navigate('/admin/anomalies')}
                  className="text-sm text-blue-400 font-mono hover:underline">
            ← Back to anomalies
          </button>
        </div>
      </DashboardShell>
    );
  }

  const sevColor = SEV_COLOR[record.anomaly.severity] ?? '#94a3b8';
  const slaColor = SLA_COLOR[record.sla.status]       ?? '#94a3b8';
  const dsColor  = DS_COLOR[record.dataset]            ?? '#64748b';

  return (
    <DashboardShell>
      {/* Breadcrumb */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/admin/anomalies')}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors font-mono"
        >
          <ArrowLeft className="w-4 h-4" /> Anomalies
        </button>
        <span className="text-slate-700">/</span>
        <span className="text-sm font-mono text-slate-300 truncate max-w-xs">{record.record_id}</span>
      </div>

      {/* Overview header */}
      <div className="rounded-2xl p-5 mb-5"
           style={{ background: 'rgba(6,14,28,0.9)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Badge label={record.dataset.toUpperCase()} color={dsColor} />
              <Badge label={record.anomaly.severity}      color={sevColor} />
              <Badge label={record.sla.status}            color={slaColor} />
              <Badge label={record.sla.priority}          color="#3b82f6" />
            </div>
            <h1 className="text-xl font-bold text-white font-mono break-all">{record.record_id}</h1>
            <p className="text-xs text-slate-500 font-mono mt-1">
              Processed: {new Date(record.timestamp).toLocaleString()} ·
              Status: <span className="text-emerald-400">{record.processing_status}</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-mono text-slate-600 uppercase mb-1">Anomaly</p>
            <div className="flex items-center gap-2">
              {record.anomaly.is_anomaly ? (
                <XCircle className="w-5 h-5 text-red-400" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              )}
              <span className={`text-sm font-mono font-bold ${record.anomaly.is_anomaly ? 'text-red-400' : 'text-emerald-400'}`}>
                {record.anomaly.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL'}
              </span>
            </div>
          </div>
        </div>

        {/* Signal chips */}
        {record.anomaly.signals.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {record.anomaly.signals.map(sig => (
              <span key={sig} className="text-[10px] font-mono px-2.5 py-1 rounded-full"
                    style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#93c5fd' }}>
                {sig}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* ML Analysis */}
        <SectionCard title="ML Analysis" icon={Activity} color="#3b82f6">
          <Field label="Model"      value={record.ml.model} />
          <Field label="Prediction" value={record.ml.prediction.toUpperCase()} color={record.ml.prediction === 'anomaly' ? '#f87171' : '#86efac'} />
          <ScoreBar label="Anomaly Score" value={record.anomaly.anomaly_score} max={1} color="#3b82f6" />
          {record.ml.reasons.length > 0 && (
            <div className="mt-3">
              <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Evidence</p>
              <BulletList items={record.ml.reasons} color="#60a5fa" />
            </div>
          )}
        </SectionCard>

        {/* Rule Analysis */}
        <SectionCard title="Rule Analysis" icon={ShieldAlert} color="#f97316">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl font-bold font-mono text-white tabular-nums">
              {record.rules.violation_count}
            </span>
            <span className="text-xs font-mono text-slate-500">rule violations</span>
          </div>
          {record.rules.rule_names.length > 0 ? (
            <div className="mb-3">
              <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Rules Triggered</p>
              <div className="flex flex-wrap gap-2">
                {record.rules.rule_names.map(rn => (
                  <span key={rn} className="text-[10px] font-mono px-2 py-1 rounded"
                        style={{ background: 'rgba(249,115,22,0.1)', color: '#fdba74', border: '1px solid rgba(249,115,22,0.2)' }}>
                    {rn.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-600 font-mono mb-3">No rule violations</p>
          )}
          {record.rules.violations.length > 0 && (
            <div>
              <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Violations</p>
              <BulletList items={record.rules.violations} color="#f97316" />
            </div>
          )}
        </SectionCard>

        {/* Bayesian Analysis */}
        <SectionCard title="Bayesian Analysis" icon={BarChart2} color="#a78bfa">
          <div className="flex items-center gap-2 mb-3">
            {record.bayesian.is_anomaly ? (
              <XCircle className="w-4 h-4 text-red-400" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            )}
            <span className={`text-xs font-mono font-medium ${record.bayesian.is_anomaly ? 'text-red-400' : 'text-emerald-400'}`}>
              {record.bayesian.is_anomaly ? 'Bayesian Anomaly' : 'Bayesian Normal'}
            </span>
          </div>
          <ScoreBar label="Probability"  value={record.bayesian.probability}  max={1}                             color="#a78bfa" />
          <ScoreBar label="Confidence"   value={record.bayesian.confidence}   max={1}                             color="#c4b5fd" />
          {record.bayesian.threshold > 0 && (
            <ScoreBar label="Threshold"  value={record.bayesian.threshold}    max={Math.max(record.bayesian.threshold * 1.5, 1)} color="#7c3aed" />
          )}
          {record.bayesian.root_causes.length > 0 && (
            <div className="mt-3">
              <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Root Causes</p>
              <BulletList items={record.bayesian.root_causes} color="#a78bfa" />
            </div>
          )}
        </SectionCard>

        {/* Data Quality */}
        <SectionCard title="Data Quality" icon={Database} color="#34d399">
          <ScoreBar label="Quality Score" value={record.quality.quality_score} max={100} color="#34d399" />
          <div className="mt-3">
            <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Issues Detected</p>
            {record.quality.issues.length > 0 ? (
              <BulletList items={record.quality.issues} color="#34d399" />
            ) : (
              <p className="text-sm text-emerald-400 font-mono">✓ No quality issues</p>
            )}
          </div>
          {/* Dataset metadata */}
          <div className="mt-4 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider mb-2">Record Context</p>
            <div className="grid grid-cols-2 gap-x-4">
              {Object.entries(record.metadata)
                .filter(([k, v]) => v && k !== 'context_for_rag')
                .slice(0, 8)
                .map(([k, v]) => (
                  <div key={k} className="mb-2">
                    <p className="text-[8px] font-mono text-slate-600 uppercase">{k.replace(/_/g, ' ')}</p>
                    <p className="text-xs font-mono text-slate-400 truncate">{v}</p>
                  </div>
                ))}
            </div>
          </div>
        </SectionCard>
      </div>

      {/* SLA + RAG full width */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        {/* SLA */}
        <SectionCard title="SLA Risk Assessment" icon={Clock} color={slaColor}>
          <div className="flex items-center gap-4 mb-4">
            <div>
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-0.5">Risk Score</p>
              <p className="text-3xl font-bold font-mono tabular-nums" style={{ color: slaColor }}>
                {record.sla.risk_score.toFixed(1)}
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <Badge label={record.sla.risk_level}  color={slaColor} />
              <Badge label={record.sla.priority}    color="#3b82f6" />
              <Badge label={record.sla.status}      color={slaColor} />
            </div>
          </div>
          <ScoreBar label="Risk Score" value={record.sla.risk_score} max={100} color={slaColor} />
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-0.5">Response Time</p>
              <p className="text-xs font-mono text-slate-300">{record.sla.response_time}</p>
            </div>
            <div>
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-0.5">Escalation</p>
              <p className={`text-xs font-mono ${record.sla.escalation_required ? 'text-red-400' : 'text-emerald-400'}`}>
                {record.sla.escalation_required ? '⚠ Required' : '✓ Not required'}
              </p>
            </div>
          </div>
          <div className="mt-3 p-3 rounded-xl" style={{ background: `${slaColor}08`, border: `1px solid ${slaColor}15` }}>
            <p className="text-[9px] font-mono text-slate-500 uppercase mb-1">Operational Recommendation</p>
            <p className="text-xs font-mono leading-relaxed" style={{ color: `${slaColor}cc` }}>
              <strong>{record.sla.action}:</strong> {record.sla.recommendation}
            </p>
          </div>
        </SectionCard>

        {/* RAG */}
        <SectionCard title="AI Recommendation" icon={Lightbulb} color="#fbbf24">
          <div className="flex items-center justify-between mb-3">
            <Badge label={`Confidence: ${(record.rag.confidence * 100).toFixed(0)}%`} color="#fbbf24" />
            <Badge label={record.rag.priority} color="#3b82f6" />
          </div>

          <div className="mb-4 p-3 rounded-xl"
               style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.12)' }}>
            <p className="text-[9px] font-mono text-slate-500 uppercase mb-1.5">Recommendation</p>
            <p className="text-xs font-mono leading-relaxed text-amber-200/80">{record.rag.recommendation}</p>
          </div>

          {record.rag.explanation && (
            <div className="mb-3">
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-1.5">Why Was This Flagged</p>
              <p className="text-xs font-mono leading-relaxed text-slate-400">{record.rag.explanation}</p>
            </div>
          )}

          {record.rag.root_cause && (
            <div className="mb-3">
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-1.5">Root Cause</p>
              <p className="text-xs font-mono leading-relaxed text-slate-400">{record.rag.root_cause}</p>
            </div>
          )}

          {record.rag.recommended_actions.length > 0 && (
            <div>
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-2">Recommended Actions</p>
              <ol className="space-y-2">
                {record.rag.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[10px] font-bold font-mono text-amber-400 flex-shrink-0 mt-0.5">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span className="text-xs font-mono leading-relaxed text-slate-400">{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {record.rag.evidence.length > 0 && (
            <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <p className="text-[9px] font-mono text-slate-600 uppercase mb-2">Supporting Evidence</p>
              <BulletList items={record.rag.evidence.slice(0, 3)} color="#fbbf24" />
            </div>
          )}
        </SectionCard>
      </div>

      {/* Processing errors */}
      {record.processing_errors.length > 0 && (
        <div className="rounded-2xl p-4"
             style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.15)' }}>
          <p className="text-[9px] font-mono text-red-400 uppercase mb-2">Processing Warnings</p>
          <BulletList items={record.processing_errors} color="#f87171" />
        </div>
      )}
    </DashboardShell>
  );
}
