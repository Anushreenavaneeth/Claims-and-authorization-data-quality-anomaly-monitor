import { useState, useEffect, FormEvent } from 'react';
import DashboardShell from '../components/DashboardShell';
import api from '../services/api';
import { UserPlus, Trash2, Loader2, CheckCircle2, AlertCircle, Eye, EyeOff } from 'lucide-react';

interface Worker {
  id: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded-full"
          style={active
            ? { background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)', color: '#4ade80' }
            : { background: 'rgba(100,116,139,0.1)', border: '1px solid rgba(100,116,139,0.2)', color: '#64748b' }
          }>
      <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-400' : 'bg-slate-500'}`} />
      {active ? 'Active' : 'Inactive'}
    </span>
  );
}

export default function WorkerManagement() {
  const [workers, setWorkers]         = useState<Worker[]>([]);
  const [loading, setLoading]         = useState(true);
  const [creating, setCreating]       = useState(false);
  const [showForm, setShowForm]       = useState(false);
  const [success, setSuccess]         = useState('');
  const [error, setError]             = useState('');
  const [showPass, setShowPass]       = useState(false);

  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [formErrors, setFormErrors]   = useState<Record<string, string>>({});

  const fetchWorkers = async () => {
    try {
      const res = await api.get('/admin/workers');
      setWorkers(res.data);
    } catch {
      setError('Failed to load workers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWorkers(); }, []);

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name.trim())    e.name     = 'Name is required.';
    if (!form.email.trim())   e.email    = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email.';
    if (!form.password)       e.password = 'Password is required.';
    else if (form.password.length < 8) e.password = 'Minimum 8 characters.';
    return e;
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setFormErrors(errs);
    if (Object.keys(errs).length) return;

    setCreating(true);
    setError(''); setSuccess('');
    try {
      await api.post('/admin/workers', form);
      setSuccess(`Worker "${form.name}" created successfully.`);
      setForm({ name: '', email: '', password: '' });
      setShowForm(false);
      fetchWorkers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Failed to create worker.');
    } finally {
      setCreating(false);
    }
  };

  const handleDeactivate = async (id: string, name: string) => {
    if (!confirm(`Deactivate worker "${name}"?`)) return;
    try {
      await api.patch(`/admin/workers/${id}/deactivate`);
      fetchWorkers();
    } catch {
      setError('Failed to deactivate worker.');
    }
  };

  const field = (key: keyof typeof form, label: string, type = 'text') => (
    <div>
      <label className="block text-[10px] font-mono tracking-widest text-slate-500 uppercase mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          type={key === 'password' ? (showPass ? 'text' : 'password') : type}
          value={form[key]}
          onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          placeholder={key === 'email' ? 'worker@org.com' : key === 'password' ? '••••••••' : 'Full name'}
          className="w-full text-sm font-mono text-slate-200 placeholder-slate-700 rounded-lg px-4 py-2.5 outline-none transition-all"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: formErrors[key] ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.08)',
          }}
          onFocus={e => { e.currentTarget.style.border = '1px solid rgba(59,130,246,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59,130,246,0.1)'; }}
          onBlur={e => { e.currentTarget.style.border = formErrors[key] ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.08)'; e.currentTarget.style.boxShadow = 'none'; }}
        />
        {key === 'password' && (
          <button type="button" onClick={() => setShowPass(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400 transition-colors">
            {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {formErrors[key] && <p className="mt-1 text-[10px] font-mono text-red-400">{formErrors[key]}</p>}
    </div>
  );

  return (
    <DashboardShell>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-[10px] font-mono tracking-widest text-slate-600 uppercase mb-1">Admin · Worker Management</p>
          <h1 className="font-display text-2xl font-bold text-white">Workers</h1>
        </div>
        <button
          onClick={() => { setShowForm(s => !s); setError(''); setSuccess(''); setFormErrors({}); }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono text-white transition-all"
          style={{ background: '#2563eb', border: '1px solid rgba(96,165,250,0.3)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = '#1d4ed8'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = '#2563eb'; }}
        >
          <UserPlus className="w-4 h-4" />
          {showForm ? 'Cancel' : 'New Worker'}
        </button>
      </div>

      {/* Feedback */}
      {success && (
        <div className="flex items-center gap-2 mb-4 px-4 py-3 rounded-lg text-sm font-mono text-emerald-400"
             style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)' }}>
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />{success}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 mb-4 px-4 py-3 rounded-lg text-sm font-mono text-red-400"
             style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <AlertCircle className="w-4 h-4 flex-shrink-0" />{error}
        </div>
      )}

      {/* Create worker form */}
      {showForm && (
        <div className="rounded-xl mb-6 p-6"
             style={{ background: 'rgba(6,14,28,0.8)', border: '1px solid rgba(59,130,246,0.2)', boxShadow: '0 0 30px rgba(59,130,246,0.05)' }}>
          <div className="h-px mb-5" style={{ background: 'linear-gradient(90deg, transparent, rgba(59,130,246,0.5), transparent)' }} />
          <h2 className="font-display text-base font-semibold text-white mb-5">Create new worker account</h2>
          <form onSubmit={handleCreate} noValidate>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
              {field('name',     'Full name')}
              {field('email',    'Email address', 'email')}
              {field('password', 'Password',      'password')}
            </div>
            <button
              type="submit" disabled={creating}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-mono text-white transition-all disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg,#2563eb,#0ea5e9)', border: '1px solid rgba(96,165,250,0.3)' }}
            >
              {creating ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Creating…</> : <><UserPlus className="w-3.5 h-3.5" />Create Worker</>}
            </button>
          </form>
        </div>
      )}

      {/* Workers table */}
      <div className="rounded-xl overflow-hidden"
           style={{ background: 'rgba(6,14,28,0.7)', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="px-5 py-3 flex items-center justify-between"
             style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-xs font-mono text-slate-400">
            {loading ? 'Loading…' : `${workers.length} worker${workers.length !== 1 ? 's' : ''}`}
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-slate-600 animate-spin" />
          </div>
        ) : workers.length === 0 ? (
          <div className="text-center py-16">
            <Users className="w-8 h-8 text-slate-700 mx-auto mb-3" />
            <p className="text-sm font-mono text-slate-600">No workers yet.</p>
            <p className="text-xs font-mono text-slate-700 mt-1">Click "New Worker" to add the first one.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                {['Name', 'Email', 'Status', 'Created', ''].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-[10px] font-mono tracking-widest text-slate-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {workers.map((w, i) => (
                <tr key={w.id}
                    style={{ borderBottom: i < workers.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.02)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                           style={{ background: 'rgba(6,182,212,0.15)', border: '1px solid rgba(6,182,212,0.25)' }}>
                        {w.name.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-slate-200 font-medium">{w.name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 font-mono text-slate-400 text-xs">{w.email}</td>
                  <td className="px-5 py-3.5"><StatusBadge active={w.is_active} /></td>
                  <td className="px-5 py-3.5 font-mono text-slate-600 text-xs">
                    {new Date(w.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    {w.is_active && (
                      <button
                        onClick={() => handleDeactivate(w.id, w.name)}
                        className="p-1.5 rounded-lg transition-all text-slate-600 hover:text-red-400"
                        style={{}}
                        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.1)'; }}
                        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                        aria-label={`Deactivate ${w.name}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </DashboardShell>
  );
}
