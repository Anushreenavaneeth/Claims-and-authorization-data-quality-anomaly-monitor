import { ReactNode, useEffect, useRef } from 'react';
import { LogOut, LayoutDashboard, ShieldAlert, Clock, Lightbulb, Users, CheckSquare, Activity, Wrench, RefreshCw } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

/* Minimal ambient canvas for dashboard bg — subtle, not competing with content */
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
      ctx.fillStyle = '#06080f';
      ctx.fillRect(0, 0, W, H);

      pts.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      });

      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
          const d = Math.sqrt(dx*dx + dy*dy);
          if (d > 280) continue;
          ctx.strokeStyle = `rgba(30,58,138,${(1 - d/280) * 0.25})`;
          ctx.lineWidth = 0.5;
          ctx.setLineDash([3, 5]);
          ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y); ctx.stroke();
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);
  return <canvas ref={ref} className="fixed inset-0 w-full h-full" style={{ zIndex: 0 }} aria-hidden="true"/>;
}

interface NavItem { icon: React.ElementType; label: string; href: string; soon?: boolean }

const ADMIN_NAV: NavItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard',         href: '/admin/dashboard' },
  { icon: ShieldAlert,     label: 'Anomalies',         href: '#', soon: true },
  { icon: Clock,           label: 'SLA Risk',          href: '#', soon: true },
  { icon: Lightbulb,       label: 'Recommendations',   href: '#', soon: true },
  { icon: Users,           label: 'Worker Management', href: '#', soon: true },
];

const WORKER_NAV: NavItem[] = [
  { icon: LayoutDashboard, label: 'Dashboard',      href: '/worker/dashboard' },
  { icon: CheckSquare,     label: 'Assigned Tasks', href: '#', soon: true },
  { icon: Activity,        label: 'Task Status',    href: '#', soon: true },
  { icon: Wrench,          label: 'Remediation',    href: '#', soon: true },
  { icon: RefreshCw,       label: 'Reprocessing',   href: '#', soon: true },
];

const THEME = {
  admin:  { accent: '#a78bfa', accentDim: 'rgba(139,92,246,0.15)', border: 'rgba(139,92,246,0.25)', dot: '#a78bfa', activeBg: 'rgba(139,92,246,0.1)'  },
  worker: { accent: '#67e8f9', accentDim: 'rgba(6,182,212,0.1)',   border: 'rgba(6,182,212,0.22)',  dot: '#22d3ee', activeBg: 'rgba(6,182,212,0.08)'   },
};

const GLASS: React.CSSProperties = {
  background: 'rgba(6,14,28,0.75)',
  border: '1px solid rgba(96,165,250,0.12)',
  backdropFilter: 'blur(16px)',
  WebkitBackdropFilter: 'blur(16px)',
};

export default function DashboardShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();
  const role      = (user?.role ?? 'worker') as 'admin' | 'worker';
  const nav       = role === 'admin' ? ADMIN_NAV : WORKER_NAV;
  const t         = THEME[role];

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      <AmbientCanvas />

      {/* ── Sidebar — glass panel, 3D left edge ── */}
      <aside
        className="relative z-10 w-56 flex-shrink-0 flex flex-col"
        style={{
          ...GLASS,
          borderRight: `1px solid ${t.border}`,
          borderTop: 'none', borderLeft: 'none', borderBottom: 'none',
          boxShadow: `4px 0 32px rgba(0,0,0,0.5), inset -1px 0 0 ${t.border}`,
        }}
      >
        {/* Logo */}
        <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid rgba(96,165,250,0.08)' }}>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                 style={{ background: t.accentDim, border: `1px solid ${t.border}` }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <path d="M3 8h4M8 3v10M13 8H9" stroke={t.accent} strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-display text-sm font-bold text-white">HDOP</span>
          </div>
          <p className="text-[9px] font-mono tracking-wider" style={{ color: 'rgba(148,163,184,0.4)' }}>
            Data Operations Platform
          </p>
        </div>

        {/* Role badge */}
        <div className="px-5 py-3">
          <span className="inline-flex items-center gap-1.5 text-[9px] font-mono tracking-widest uppercase px-2 py-1 rounded"
                style={{ background: t.accentDim, border: `1px solid ${t.border}`, color: t.accent }}>
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: t.dot }}/>
            {role} console
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-2" aria-label="Sidebar">
          {nav.map(({ icon: Icon, label, href, soon }) => {
            const active = location.pathname === href;
            return (
              <button
                key={label}
                onClick={() => href !== '#' && navigate(href)}
                disabled={soon}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 text-xs font-mono text-left transition-all"
                style={active
                  ? { background: t.activeBg, color: t.accent, border: `1px solid ${t.border}` }
                  : soon
                  ? { color: 'rgba(100,116,139,0.4)', cursor: 'default' }
                  : { color: 'rgba(148,163,184,0.6)', border: '1px solid transparent' }
                }
                onMouseEnter={e => { if (!active && !soon) { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.03)'; (e.currentTarget as HTMLElement).style.color = '#e2e8f0'; }}}
                onMouseLeave={e => { if (!active && !soon) { (e.currentTarget as HTMLElement).style.background = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'rgba(148,163,184,0.6)'; }}}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="flex-1">{label}</span>
                {soon && <span className="text-[8px] opacity-40 uppercase tracking-wider">soon</span>}
              </button>
            );
          })}
        </nav>

        {/* User card */}
        <div className="p-3" style={{ borderTop: '1px solid rgba(96,165,250,0.08)' }}>
          <div className="rounded-xl p-3"
               style={{ background: 'rgba(0,0,0,0.3)', border: `1px solid ${t.border}` }}>
            <div className="flex items-center justify-between mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center font-display font-bold text-sm text-white"
                   style={{ background: t.accentDim, border: `1px solid ${t.border}` }}>
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <button
                onClick={() => { logout(); navigate('/login', { replace: true }); }}
                aria-label="Logout"
                className="p-1.5 rounded-lg transition-all"
                style={{ color: 'rgba(100,116,139,0.6)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#f87171'; (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.1)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'rgba(100,116,139,0.6)'; (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs font-mono text-slate-300 font-medium truncate">{user?.name}</p>
            <p className="text-[10px] font-mono truncate mt-0.5" style={{ color: 'rgba(148,163,184,0.4)' }}>
              {user?.email}
            </p>
          </div>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="relative z-10 flex-1 flex flex-col min-w-0">

        {/* Top bar — glass strip */}
        <header
          className="h-12 flex items-center justify-between px-8"
          style={{ ...GLASS, borderBottom: `1px solid ${t.border}`, borderLeft: 'none', borderRight: 'none', borderTop: 'none' }}
        >
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: t.dot }}/>
            <span className="text-[10px] font-mono" style={{ color: 'rgba(148,163,184,0.4)' }}>
              {location.pathname.replace(/\//g, ' › ').slice(3)}
            </span>
          </div>
          <span className="text-[10px] font-mono" style={{ color: 'rgba(100,116,139,0.4)' }}>
            {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
          </span>
        </header>

        {/* Content — glass-panel wrapped */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <div
            className="min-h-full rounded-2xl p-8"
            style={{
              background: 'rgba(6,14,28,0.55)',
              border: `1px solid ${t.border}`,
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              boxShadow: `0 0 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.02)`,
            }}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
