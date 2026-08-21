import { useState, type FormEvent, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

/* ─────────────────────────────────────────────
   PARTICLE NETWORK CANVAS
   Draws animated healthcare-node network
───────────────────────────────────────────── */
function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    let W = canvas.width  = window.innerWidth;
    let H = canvas.height = window.innerHeight;

    const onResize = () => {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', onResize);

    const ICONS = [
      (cx: number, cy: number, r: number, c: CanvasRenderingContext2D) => {
        c.beginPath();
        c.rect(cx - r * 0.15, cy - r * 0.55, r * 0.3, r * 1.1);
        c.rect(cx - r * 0.55, cy - r * 0.15, r * 1.1, r * 0.3);
        c.fill();
      },
      (cx: number, cy: number, r: number, c: CanvasRenderingContext2D) => {
        const s = r * 0.6;
        c.beginPath();
        c.moveTo(cx, cy + s * 0.8);
        c.bezierCurveTo(cx - s * 1.2, cy - s * 0.2, cx - s * 1.4, cy - s * 1.2, cx, cy - s * 0.3);
        c.bezierCurveTo(cx + s * 1.4, cy - s * 1.2, cx + s * 1.2, cy - s * 0.2, cx, cy + s * 0.8);
        c.fill();
      },
      (cx: number, cy: number, r: number, c: CanvasRenderingContext2D) => {
        const w = r * 0.9, h = r * 0.38;
        c.beginPath();
        c.roundRect(cx - w, cy - h, w * 2, h * 2, h);
        c.fill();
        c.beginPath();
        c.moveTo(cx, cy - h); c.lineTo(cx, cy + h);
        c.stroke();
      },
      (cx: number, cy: number, r: number, c: CanvasRenderingContext2D) => {
        for (let i = 0; i < 5; i++) {
          const t = (i / 4) * Math.PI * 2;
          const dx = Math.sin(t) * r * 0.4;
          c.beginPath();
          c.arc(cx + dx, cy - r * 0.5 + i * r * 0.25, r * 0.1, 0, Math.PI * 2);
          c.fill();
          c.beginPath();
          c.arc(cx - dx, cy - r * 0.5 + i * r * 0.25, r * 0.1, 0, Math.PI * 2);
          c.fill();
        }
      },
      (cx: number, cy: number, r: number, c: CanvasRenderingContext2D) => {
        c.beginPath();
        c.arc(cx, cy + r * 0.2, r * 0.35, 0, Math.PI * 2);
        c.stroke();
        c.beginPath();
        c.moveTo(cx - r * 0.35, cy + r * 0.2);
        c.lineTo(cx - r * 0.35, cy - r * 0.4);
        c.arc(cx, cy - r * 0.4, r * 0.35, Math.PI, 0);
        c.lineTo(cx + r * 0.35, cy - r * 0.1);
        c.stroke();
      },
    ];

    interface Node {
      x: number; y: number; z: number;
      vx: number; vy: number;
      r: number;
      icon: number;
      alpha: number;
      pulse: number;
      pulseSpeed: number;
      glowSize: number;
    }

    const COUNT = 28;
    const nodes: Node[] = Array.from({ length: COUNT }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      z: Math.random(),
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: 18 + Math.random() * 22,
      icon: Math.floor(Math.random() * ICONS.length),
      alpha: 0.4 + Math.random() * 0.5,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: 0.012 + Math.random() * 0.018,
      glowSize: 30 + Math.random() * 40,
    }));

    let raf: number;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      const bg = ctx.createRadialGradient(W * 0.35, H * 0.45, 0, W * 0.5, H * 0.5, W * 0.8);
      bg.addColorStop(0, '#061428');
      bg.addColorStop(0.5, '#030a14');
      bg.addColorStop(1, '#010408');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      const orb = ctx.createRadialGradient(W * 0.38, H * 0.42, 0, W * 0.38, H * 0.42, 200);
      orb.addColorStop(0, 'rgba(255,160,60,0.18)');
      orb.addColorStop(0.4, 'rgba(59,130,246,0.08)');
      orb.addColorStop(1, 'transparent');
      ctx.fillStyle = orb;
      ctx.fillRect(0, 0, W, H);

      nodes.forEach(n => {
        n.x += n.vx; n.y += n.vy;
        n.pulse += n.pulseSpeed;
        if (n.x < -60) n.x = W + 60;
        if (n.x > W + 60) n.x = -60;
        if (n.y < -60) n.y = H + 60;
        if (n.y > H + 60) n.y = -60;
      });

      ctx.save();
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = 200;
          if (dist > maxDist) continue;
          const alpha = (1 - dist / maxDist) * 0.35;
          ctx.strokeStyle = `rgba(96,165,250,${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.setLineDash([5, 4]);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
          if (dist < 120) {
            ctx.setLineDash([]);
            ctx.fillStyle = `rgba(147,197,253,${alpha * 0.8})`;
            ctx.beginPath();
            ctx.arc((a.x + b.x) / 2, (a.y + b.y) / 2, 2, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
      ctx.restore();

      nodes.forEach(n => {
        const pulseFactor = 1 + Math.sin(n.pulse) * 0.08;
        const scale = 0.5 + n.z * 0.7;
        const r = n.r * scale * pulseFactor;
        const alpha = n.alpha * (0.85 + n.z * 0.15);

        const glow = ctx.createRadialGradient(n.x, n.y, r * 0.3, n.x, n.y, r + n.glowSize * scale);
        glow.addColorStop(0, `rgba(59,130,246,${alpha * 0.25})`);
        glow.addColorStop(1, 'transparent');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + n.glowSize * scale, 0, Math.PI * 2);
        ctx.fill();

        ctx.save();
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = `rgba(147,197,253,${alpha * 0.7})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([2, 4]);
        ctx.strokeStyle = `rgba(96,165,250,${alpha * 0.3})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, r * 1.3, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        ctx.save();
        ctx.fillStyle = `rgba(186,230,253,${alpha * 0.85})`;
        ctx.strokeStyle = `rgba(186,230,253,${alpha * 0.85})`;
        ctx.lineWidth = 1.2;
        ctx.setLineDash([]);
        ICONS[n.icon](n.x, n.y, r * 0.55, ctx);
        ctx.restore();
      });

      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    />
  );
}

/* ─────────────────────────────────────────────
   MAIN LOGIN PAGE
───────────────────────────────────────────── */
function validate(email: string, password: string) {
  const e: Record<string, string> = {};
  if (!email) e.email = 'Email is required.';
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Enter a valid email.';
  if (!password) e.password = 'Password is required.';
  return e;
}

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [apiError, setApiError] = useState('');
  const [loading,  setLoading]  = useState(false);
  const [touched,  setTouched]  = useState({ email: false, password: false });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const errs = validate(email, password);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    if (errs.email || errs.password) return;
    setLoading(true);
    setApiError('');
    try {
      await login(email, password);
      navigate('/', { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Connection error. Try again.';
      setApiError(message === 'Invalid credentials' ? 'Invalid credentials.' : message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center overflow-hidden relative">

      {/* Animated particle background */}
      <ParticleCanvas />

      {/* Glassmorphism login card */}
      <div className="relative z-10 w-full flex items-center justify-center px-4 py-12">
        <div>
          {/* Glow ring behind card */}
          <div
            className="absolute -inset-6 rounded-3xl opacity-40 blur-2xl pointer-events-none"
            style={{
              background: 'radial-gradient(ellipse at 40% 50%, rgba(59,130,246,0.5) 0%, rgba(14,165,233,0.2) 50%, transparent 80%)',
            }}
            aria-hidden="true"
          />

          {/* Card */}
          <div
            className="relative w-[420px] max-w-[92vw] rounded-2xl overflow-hidden"
            style={{
              background: 'rgba(6,14,28,0.82)',
              border: '1px solid rgba(96,165,250,0.18)',
              boxShadow: '0 0 0 1px rgba(96,165,250,0.06), 0 32px 80px rgba(0,0,0,0.7), 0 0 60px rgba(59,130,246,0.08)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
            }}
          >
            {/* Top accent line */}
            <div className="h-[2px] w-full"
                 style={{ background: 'linear-gradient(90deg, transparent, rgba(96,165,250,0.8), rgba(14,165,233,0.6), transparent)' }}
            />

            <div className="px-9 pt-9 pb-10">

              {/* Wordmark */}
              <div className="flex items-center gap-2.5 mb-8">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                     style={{ background: 'rgba(37,99,235,0.25)', border: '1px solid rgba(96,165,250,0.3)' }}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="M3 8h4M8 3v10M13 8H9" stroke="#60a5fa" strokeWidth="1.8" strokeLinecap="round"/>
                  </svg>
                </div>
                <div>
                  <p className="font-display text-sm font-bold text-white tracking-tight leading-none">Claims Monitor</p>
                  <p className="text-[9px] font-mono text-blue-400/60 tracking-widest uppercase leading-none mt-0.5">Healthcare Data Ops</p>
                </div>

                {/* Live ping */}
                <div className="ml-auto flex items-center gap-1.5">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"/>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"/>
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400/70">online</span>
                </div>
              </div>

              {/* Heading */}
              <h1 className="font-display text-2xl font-bold text-white mb-1 leading-tight">
                Operator access
              </h1>
              <p className="text-xs font-mono text-blue-300/40 mb-7 tracking-wide">
                Authenticate to enter the platform
              </p>

              {/* API error */}
              {apiError && (
                <div role="alert"
                     className="mb-5 px-4 py-2.5 rounded-lg text-xs font-mono text-red-400"
                     style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                  ✗ &nbsp;{apiError}
                </div>
              )}

              <form onSubmit={handleSubmit} noValidate aria-label="Login form">
                {/* Email */}
                <div className="mb-4">
                  <label htmlFor="email"
                         className="block text-[10px] font-mono tracking-[0.15em] text-blue-300/50 uppercase mb-2">
                    Email
                  </label>
                  <input
                    id="email" type="email" autoComplete="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    onBlur={() => setTouched(t => ({ ...t, email: true }))}
                    placeholder="operator@org.com"
                    className="w-full text-sm font-mono text-slate-200 placeholder-slate-600 rounded-lg px-4 py-2.5 outline-none transition-all"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      border: touched.email && errs.email
                        ? '1px solid rgba(239,68,68,0.5)'
                        : '1px solid rgba(96,165,250,0.15)',
                      boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)',
                    }}
                  />
                  {touched.email && errs.email && (
                    <p role="alert" className="mt-1 text-[10px] font-mono text-red-400">{errs.email}</p>
                  )}
                </div>

                {/* Password */}
                <div className="mb-7">
                  <label htmlFor="password"
                         className="block text-[10px] font-mono tracking-[0.15em] text-blue-300/50 uppercase mb-2">
                    Password
                  </label>
                  <input
                    id="password" type="password" autoComplete="current-password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onBlur={() => setTouched(t => ({ ...t, password: true }))}
                    placeholder="••••••••••••"
                    className="w-full text-sm font-mono text-slate-200 placeholder-slate-700 rounded-lg px-4 py-2.5 outline-none transition-all"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      border: touched.password && errs.password
                        ? '1px solid rgba(239,68,68,0.5)'
                        : '1px solid rgba(96,165,250,0.15)',
                      boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)',
                    }}
                  />
                  {touched.password && errs.password && (
                    <p role="alert" className="mt-1 text-[10px] font-mono text-red-400">{errs.password}</p>
                  )}
                </div>

                {/* Submit */}
                <button
                  type="submit" disabled={loading}
                  id="login-submit-btn"
                  className="w-full py-3 rounded-lg text-sm font-mono font-semibold text-white transition-all disabled:opacity-50 relative overflow-hidden group"
                  style={{
                    background: 'linear-gradient(135deg, rgba(37,99,235,0.9), rgba(14,116,144,0.9))',
                    border: '1px solid rgba(96,165,250,0.3)',
                    boxShadow: '0 0 20px rgba(59,130,246,0.2), inset 0 1px 0 rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        style={{ background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.07) 50%, transparent 100%)' }}
                        aria-hidden="true"/>
                  <span className="relative flex items-center justify-center gap-2">
                    {loading
                      ? <><Loader2 className="w-3.5 h-3.5 animate-spin"/>authenticating…</>
                      : <>authenticate <span aria-hidden="true">→</span></>}
                  </span>
                </button>
              </form>

              {/* Dev credential picker */}
              <div className="mt-6 pt-5" style={{ borderTop: '1px solid rgba(96,165,250,0.08)' }}>
                <p className="text-[9px] font-mono text-slate-700 uppercase tracking-widest mb-2">
                  Dev credentials
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { role: 'admin',  email: 'admin@example.com',  pass: 'Admin1234!',  color: 'rgba(139,92,246,0.15)', border: 'rgba(139,92,246,0.3)', text: '#a78bfa' },
                    { role: 'worker', email: 'worker@example.com', pass: 'Worker1234!', color: 'rgba(6,182,212,0.1)',   border: 'rgba(6,182,212,0.25)', text: '#67e8f9' },
                  ].map(c => (
                    <button
                      key={c.role} type="button"
                      onClick={() => { setEmail(c.email); setPassword(c.pass); setApiError(''); }}
                      className="rounded-lg px-3 py-2 text-left transition-all hover:scale-[1.02] active:scale-[0.98]"
                      style={{ background: c.color, border: `1px solid ${c.border}` }}
                    >
                      <span className="block text-[9px] font-mono uppercase tracking-widest mb-0.5"
                            style={{ color: c.text }}>{c.role}</span>
                      <span className="block text-[10px] font-mono text-slate-400 truncate">{c.email}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
