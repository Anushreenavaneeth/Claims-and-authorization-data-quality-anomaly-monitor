import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function AccessDenied() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const home = user?.role === 'admin' ? '/admin/dashboard' : '/worker/dashboard';

  return (
    <div className="min-h-screen bg-[#06080f] flex items-center justify-center px-8">
      <div
        className="max-w-xs w-full rounded-2xl p-10"
        style={{
          background: 'rgba(6,14,28,0.82)',
          border: '1px solid rgba(239,68,68,0.2)',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 0 60px rgba(239,68,68,0.06), 0 32px 80px rgba(0,0,0,0.6)',
        }}
      >
        {/* Top accent */}
        <div className="h-px mb-8" style={{ background: 'linear-gradient(90deg, transparent, rgba(239,68,68,0.6), transparent)' }}/>

        <p className="text-[10px] font-mono tracking-[0.2em] uppercase mb-4" style={{ color: 'rgba(239,68,68,0.6)' }}>
          403 · forbidden
        </p>
        <h1 className="font-display text-3xl font-bold text-white mb-3 leading-tight">
          Access<br/>denied.
        </h1>
        <div className="w-10 h-px mb-5" style={{ background: 'rgba(239,68,68,0.3)' }}/>
        <p className="text-xs font-mono text-slate-500 leading-relaxed mb-8">
          You don't have the required role to view this resource. Contact your administrator if this is an error.
        </p>
        <button
          onClick={() => navigate(home, { replace: true })}
          className="text-xs font-mono flex items-center gap-2 group transition-colors"
          style={{ color: 'rgba(148,163,184,0.5)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#e2e8f0'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'rgba(148,163,184,0.5)'; }}
        >
          <span className="transition-transform group-hover:-translate-x-0.5">←</span>
          back to my dashboard
        </button>
      </div>
    </div>
  );
}
