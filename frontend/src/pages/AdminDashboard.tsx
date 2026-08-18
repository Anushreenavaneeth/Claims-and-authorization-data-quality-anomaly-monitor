import { useAuth } from '../auth/AuthContext';
import DashboardShell from '../components/DashboardShell';
import { ShieldAlert, Clock, Lightbulb, Users, Database } from 'lucide-react';

/* 3D floating stat card */
function StatCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div
      className="rounded-xl p-4 transition-all duration-300 hover:-translate-y-1"
      style={{
        background: `linear-gradient(135deg, rgba(6,14,28,0.9), rgba(10,20,40,0.8))`,
        border: `1px solid ${color}33`,
        boxShadow: `0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px ${color}11, inset 0 1px 0 ${color}15`,
      }}
    >
      <p className="text-[9px] font-mono uppercase tracking-widest mb-2" style={{ color: `${color}90` }}>{label}</p>
      <p className="font-display text-2xl font-bold text-white mb-0.5">{value}</p>
      <p className="text-[10px] font-mono" style={{ color: 'rgba(148,163,184,0.45)' }}>{sub}</p>
      {/* Bottom glow strip */}
      <div className="h-px mt-3 rounded-full" style={{ background: `linear-gradient(90deg, transparent, ${color}60, transparent)` }}/>
    </div>
  );
}

const MODULES = [
  { icon: Database,      label: 'Data Quality',       desc: 'Schema drift, null-rate spikes, cross-field validation.',  color: '#60a5fa', tag: 'pipeline' },
  { icon: ShieldAlert,   label: 'Anomaly Detection',  desc: 'ML-scored outliers against rolling baselines per source.', color: '#a78bfa', tag: 'ml'       },
  { icon: Clock,         label: 'SLA Risk',            desc: 'Predictive breach scoring with configurable thresholds.',  color: '#f87171', tag: 'risk'     },
  { icon: Lightbulb,     label: 'Recommendations',     desc: 'AI remediation paths ranked by impact × confidence.',     color: '#fbbf24', tag: 'ai'       },
  { icon: Users,         label: 'Worker Management',   desc: 'Task assignment, escalation, and progress tracking.',      color: '#34d399', tag: 'ops'      },
];

export default function AdminDashboard() {
  const { user } = useAuth();

  return (
    <DashboardShell>
      {/* Header */}
      <div className="mb-8">
        <p className="text-[10px] font-mono tracking-[0.2em] text-slate-600 uppercase mb-2">Admin · Dashboard</p>
        <div className="flex items-end justify-between">
          <h1 className="font-display text-3xl font-bold text-white leading-tight">
            {user?.name?.split(' ')[0]}, you're in.
          </h1>
          <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"/>
            authenticated
          </span>
        </div>
      </div>

      {/* 3D floating stat cards */}
      <div className="grid grid-cols-3 gap-3 mb-8">
        <StatCard label="Claims ingested"  value="3.4M"   sub="↑ 12% this week"    color="#60a5fa"/>
        <StatCard label="Active anomalies" value="127"    sub="3 critical pending"  color="#f87171"/>
        <StatCard label="SLA compliance"   value="99.2%"  sub="above 98% target"   color="#34d399"/>
      </div>

      {/* Module rows — numbered, NOT icon-tile cards */}
      <div style={{ borderTop: '1px solid rgba(96,165,250,0.08)' }} className="pt-6">
        <p className="text-[9px] font-mono tracking-[0.22em] text-slate-600 uppercase mb-4">
          Upcoming modules — {MODULES.length} planned
        </p>
        <div className="space-y-0" style={{ borderBottom: '1px solid rgba(96,165,250,0.06)' }}>
          {MODULES.map((m, i) => (
            <div
              key={m.label}
              className="group flex items-center gap-5 py-3.5 px-3 -mx-3 rounded-xl cursor-default transition-all"
              style={{ borderTop: '1px solid rgba(96,165,250,0.06)' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.02)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
            >
              {/* Number */}
              <span className="font-display text-xl font-bold w-8 flex-shrink-0 tabular-nums leading-none"
                    style={{ color: 'rgba(148,163,184,0.15)' }}>
                {String(i + 1).padStart(2, '0')}
              </span>

              {/* Icon bubble */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-110"
                   style={{ background: `${m.color}12`, border: `1px solid ${m.color}30` }}>
                <m.icon className="w-3.5 h-3.5" style={{ color: m.color }}/>
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-display font-semibold text-slate-200">{m.label}</p>
                <p className="text-[11px] font-mono text-slate-500 leading-relaxed">{m.desc}</p>
              </div>

              {/* Tag + soon */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-[9px] font-mono px-2 py-0.5 rounded-full"
                      style={{ background: `${m.color}12`, border: `1px solid ${m.color}25`, color: m.color }}>
                  {m.tag}
                </span>
                <span className="text-[9px] font-mono text-slate-700 uppercase tracking-wider">soon</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
