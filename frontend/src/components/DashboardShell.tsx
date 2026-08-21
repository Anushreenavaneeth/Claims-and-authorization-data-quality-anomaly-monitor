import { ReactNode, useEffect, useRef } from 'react';
import {
  LayoutDashboard, Activity, AlertTriangle, Clock,
  Database, ShieldCheck, Layers, Pill, FileCheck,
  Sparkles, BarChart2, LogOut, Users,
  CheckSquare, Wrench, RefreshCw,
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAnomalyCount } from '../hooks/useAnomalyCount';

/* ── Ambient canvas bg ── */
function AmbientCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext('2d')!;
    let W = c.width = window.innerWidth;
    let H = c.height = window.innerHeight;
    const resize = () => { W = c.width = window.innerWidth; H = c.height = window.innerHeight; };
    window.addEventListener('resize', resize);
    const pts = Array.from({ length: 14 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.2, vy: (Math.random() - 0.5) * 0.2,
    }));
    let raf: number;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = '#0b0f1a'; ctx.fillRect(0, 0, W, H);
      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      });
      for (let i = 0; i < pts.length; i++)
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d > 260) continue;
          ctx.strokeStyle = `rgba(30,58,138,${(1 - d / 260) * 0.2})`;
          ctx.lineWidth = 0.5; ctx.setLineDash([3, 5]);
          ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke();
        }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);
  return <canvas ref={ref} className="fixed inset-0 w-full h-full" style={{ zIndex: 0 }} aria-hidden="true" />;
}

/* ── Nav types ── */
interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  badge?: number;
  badgeColor?: string;
  soon?: boolean;
}
interface NavGroup { section: string; items: NavItem[] }

/* ── Worker nav ── */
const WORKER_GROUPS: NavGroup[] = [
  {
    section: 'WORK',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard',      href: '/worker/dashboard' },
      { icon: CheckSquare,     label: 'Assigned Tasks', href: '#', soon: true },
      { icon: Activity,        label: 'Task Status',    href: '#', soon: true },
    ],
  },
  {
    section: 'ACTIONS',
    items: [
      { icon: Wrench,     label: 'Remediation',  href: '#', soon: true },
      { icon: RefreshCw,  label: 'Reprocessing', href: '#', soon: true },
    ],
  },
];

export default function DashboardShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const role     = (user?.role ?? 'worker') as 'admin' | 'worker';
  const { openCount, connected } = useAnomalyCount();

  // Build nav groups with live anomaly count injected
  const ADMIN_GROUPS_LIVE: NavGroup[] = [
    {
      section: 'MONITOR',
      items: [
        { icon: LayoutDashboard, label: 'Dashboard',          href: '/admin/dashboard' },
        { icon: Activity,        label: 'Pipeline Monitoring', href: '#', soon: true },
        { icon: AlertTriangle,   label: 'Anomalies',           href: '/admin/anomalies',
          badge: openCount > 0 ? openCount : undefined, badgeColor: '#ef4444' },
        { icon: Clock,           label: 'SLA Monitoring',      href: '#', soon: true },
      ],
    },
    {
      section: 'DATA',
      items: [
        { icon: Database,    label: 'Data Sources',       href: '/admin/data-sources' },
        { icon: ShieldCheck, label: 'Data Quality Rules', href: '#', soon: true },
        { icon: Layers,      label: 'Claims',             href: '#', soon: true },
        { icon: Pill,        label: 'Pharmacy',           href: '#', soon: true },
        { icon: FileCheck,   label: 'Authorizations',     href: '#', soon: true },
      ],
    },
    {
      section: 'INSIGHTS',
      items: [
        { icon: Sparkles,  label: 'AI Insights', href: '#', soon: true },
        { icon: BarChart2, label: 'Reports',     href: '#', soon: true },
      ],
    },
    {
      section: 'ADMIN',
      items: [
        { icon: Users, label: 'Worker Management', href: '/admin/workers' },
      ],
    },
  ];

  const groups = role === 'admin' ? ADMIN_GROUPS_LIVE : WORKER_GROUPS;

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      <AmbientCanvas />

      {/* ── Sidebar ── */}
      <aside
        className="relative z-10 w-60 flex-shrink-0 flex flex-col select-none"
        style={{
          background: 'rgba(10,14,26,0.92)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
        }}
      >
        {/* Brand */}
        <div className="px-5 pt-6 pb-5 flex items-center gap-3"
             style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
               style={{ background: 'linear-gradient(135deg,#2563eb,#0ea5e9)' }}>
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white leading-tight">DQ MONITOR</p>
            <p className="text-[9px] text-slate-500 leading-tight">Claims &amp; Authorization<br />Data Operations</p>
          </div>
        </div>

        {/* Grouped nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-3" aria-label="Sidebar">
          {groups.map(group => (
            <div key={group.section} className="mb-4">
              <p className="text-[9px] font-semibold tracking-[0.15em] text-slate-500 uppercase px-2 mb-1.5">
                {group.section}
              </p>
              {group.items.map(({ icon: Icon, label, href, badge, badgeColor, soon }) => {
                const active = location.pathname === href;
                return (
                  <button
                    key={label}
                    onClick={() => !soon && href !== '#' && navigate(href)}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 text-sm text-left transition-all group"
                    style={
                      active
                        ? { background: '#2563eb', color: '#fff' }
                        : soon
                        ? { color: 'rgba(100,116,139,0.45)', cursor: 'default' }
                        : { color: 'rgba(203,213,225,0.75)' }
                    }
                    onMouseEnter={e => { if (!active && !soon) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.06)'; }}
                    onMouseLeave={e => { if (!active && !soon) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className="flex-1 text-[13px]">{label}</span>
                    {badge !== undefined && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full text-white min-w-[20px] text-center"
                            style={{ background: badgeColor ?? '#3b82f6' }}>
                        {badge}
                      </span>
                    )}
                    {soon && !badge && (
                      <span className="text-[8px] text-slate-600 uppercase tracking-wider">soon</span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 pb-3" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="px-3 py-2 mb-1">
            <p className="text-xs text-slate-200 font-medium truncate">{user?.name}</p>
            <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => { logout(); navigate('/login', { replace: true }); }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all"
            style={{ color: 'rgba(203,213,225,0.6)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#f87171'; (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.08)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'rgba(203,213,225,0.6)'; (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
          >
            <LogOut className="w-4 h-4" />
            <span className="text-[13px]">Logout</span>
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="relative z-10 flex-1 flex flex-col min-w-0">
        <header
          className="h-12 flex items-center justify-between px-7"
          style={{ background: 'rgba(10,14,26,0.7)', borderBottom: '1px solid rgba(255,255,255,0.05)', backdropFilter: 'blur(12px)' }}
        >
          <span className="text-[11px] font-mono text-slate-500">
            {location.pathname.replace(/\//g, ' / ').slice(3)}
          </span>
          <div className="flex items-center gap-3">
            {role === 'admin' && (
              <span className="flex items-center gap-1.5 text-[10px] font-mono"
                    style={{ color: connected ? '#4ade80' : '#64748b' }}>
                <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}/>
                {connected ? 'live' : 'offline'}
              </span>
            )}
            <span className="text-[11px] font-mono text-slate-600">
              {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
        </header>
        <main className="flex-1 p-6 lg:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
