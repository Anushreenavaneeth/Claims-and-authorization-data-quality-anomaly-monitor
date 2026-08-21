import { useState, useEffect } from 'react';
import {
  Bell, Mail, ShieldAlert, Clock, UserPlus, CheckCircle2,
  AlertCircle, Server, Send, Loader2, RefreshCw, History, Key
} from 'lucide-react';
import {
  getNotificationSettings, updateNotificationSettings, testSMTPConnection,
  type NotificationSettingsData
} from '../services/api';

export function NotificationSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettingsData>({
    email_notifications_enabled: true,
    worker_invitations: true,
    critical_anomalies: true,
    sla_at_risk: true,
    sla_breached: true,
    pipeline_failures: true,
    worker_assignments: true,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_password_configured: false,
    smtp_from_email: 'notifications@healthdata-ops.internal',
    smtp_from_name: 'Healthcare DQ Monitor',
    smtp_use_tls: true,
    admin_alert_email: 'admin@healthdata-ops.internal',
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await getNotificationSettings();
      setSettings(data);
      if (data.admin_alert_email) {
        setTestEmail(data.admin_alert_email);
      }
    } catch {
      // Keep defaults
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (key: keyof NotificationSettingsData) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const saved = await updateNotificationSettings(settings);
      setSettings(saved);
      setSuccessMsg('Operational notification preferences and SMTP settings saved successfully.');
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch {
      setErrorMsg('Failed to save notification settings. Please check server logs.');
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail.trim()) {
      setErrorMsg('Please enter a recipient email address to send the verification message.');
      return;
    }
    setTesting(true);
    setTestResult(null);
    setErrorMsg(null);
    try {
      const res = await testSMTPConnection(testEmail, settings);
      setTestResult({
        success: res.success,
        message: res.message,
      });
      if (res.success) {
        setSuccessMsg(`Test verification email dispatched to ${testEmail}.`);
        setTimeout(() => setSuccessMsg(null), 5000);
      } else {
        setErrorMsg(res.message);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'SMTP connection test failed.';
      setTestResult({ success: false, message: msg });
      setErrorMsg(msg);
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight">Notification & SMTP Settings</h1>
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200 font-medium">
              Admin & Relay Control
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-normal">
            Configure automated email dispatch pipelines, critical alert triggers, and SMTP mail relay credentials.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadSettings}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-all shadow-2xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-sans font-semibold text-white transition-all disabled:opacity-50 shadow-sm hover:bg-blue-700 active:scale-[0.99]"
            style={{ background: '#2563eb' }}
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            <span>Save Preferences</span>
          </button>
        </div>
      </div>

      {/* Status Banners */}
      {successMsg && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg text-xs font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 shadow-xs">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg text-xs font-mono text-red-800 bg-red-50 border border-red-200 shadow-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Notification Channel & Trigger Toggles (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          
          {/* Master Toggle Card */}
          <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  settings.email_notifications_enabled ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'bg-slate-100 text-slate-400'
                }`}>
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Master Email Notifications</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {settings.email_notifications_enabled
                      ? 'System email dispatch engine is globally ACTIVE'
                      : 'All outgoing email dispatches are paused'}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleToggle('email_notifications_enabled')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  settings.email_notifications_enabled ? 'bg-blue-600' : 'bg-slate-300'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.email_notifications_enabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {/* Trigger Channels Card */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-mono uppercase tracking-widest text-slate-700 font-bold">
                  Operational Alert Triggers
                </h3>
              </div>
              <span className="text-[11px] font-mono text-slate-400">Granular Policies</span>
            </div>

            <div className="divide-y divide-slate-100">
              
              {/* Worker Invitations */}
              <div className="p-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100 mt-0.5">
                    <UserPlus className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Worker & Operator Invitations</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Sends onboarding email with password setup link when Admin creates a worker account.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('worker_invitations')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    settings.worker_invitations ? 'bg-emerald-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    settings.worker_invitations ? 'translate-x-4.5' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              {/* Critical Anomalies */}
              <div className="p-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-rose-50 text-rose-600 border border-rose-100 mt-0.5">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Critical Quality Anomalies</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Dispatches high-urgency notifications to assigned stewards when Isolation Forest detects severe outliers.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('critical_anomalies')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    settings.critical_anomalies ? 'bg-rose-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    settings.critical_anomalies ? 'translate-x-4.5' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              {/* SLA At Risk */}
              <div className="p-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-amber-50 text-amber-600 border border-amber-100 mt-0.5">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">SLA At Risk Warnings</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Alerts data stewards when an anomaly processing time approaches 75% of target turnaround SLA.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('sla_at_risk')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    settings.sla_at_risk ? 'bg-amber-500' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    settings.sla_at_risk ? 'translate-x-4.5' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              {/* SLA Breached */}
              <div className="p-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-red-50 text-red-600 border border-red-100 mt-0.5">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">SLA Breach Incidents</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Sends immediate escalation email to Operations Admin when a claim exceeds maximum allowable resolution SLA.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('sla_breached')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    settings.sla_breached ? 'bg-red-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    settings.sla_breached ? 'translate-x-4.5' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              {/* Worker Task Assignment */}
              <div className="p-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800">Worker Task Assignments</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Notifies an operator when an admin assigns an anomaly record to their review queue.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('worker_assignments')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none ${
                    settings.worker_assignments ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                    settings.worker_assignments ? 'translate-x-4.5' : 'translate-x-1'
                  }`} />
                </button>
              </div>

            </div>
          </div>

          {/* Audit Logging Notice */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3 text-xs text-slate-600">
            <History className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-800">Audit Trail Integration: </span>
              Every dispatched email notification is permanently recorded in the immutable Audit Log with recipient email, alert type, and delivery confirmation for full HIPAA compliance.
            </div>
          </div>

        </div>

        {/* Right Column: SMTP Server Configuration (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          
          {/* SMTP Credentials Card */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-mono uppercase tracking-widest text-slate-700 font-bold">
                  SMTP Relay Credentials
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                Backend Enforced
              </span>
            </div>

            {/* Host & Port */}
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 font-semibold">
                  SMTP Host
                </label>
                <input
                  type="text"
                  value={settings.smtp_host || ''}
                  onChange={e => setSettings(s => ({ ...s, smtp_host: e.target.value }))}
                  placeholder="smtp.gmail.com"
                  className="w-full text-xs font-mono text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 font-semibold">
                  Port
                </label>
                <input
                  type="number"
                  value={settings.smtp_port || 587}
                  onChange={e => setSettings(s => ({ ...s, smtp_port: parseInt(e.target.value) || 587 }))}
                  className="w-full text-xs font-mono text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
                />
              </div>
            </div>

            {/* Username / From Email */}
            <div>
              <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 font-semibold">
                SMTP Username / Email
              </label>
              <input
                type="text"
                value={settings.smtp_username || ''}
                onChange={e => setSettings(s => ({ ...s, smtp_username: e.target.value }))}
                placeholder="notifications@yourdomain.com"
                className="w-full text-xs font-sans text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
              />
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
                  SMTP Password / App Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-[10px] font-mono text-blue-600 hover:underline"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={settings.smtp_password || ''}
                onChange={e => setSettings(s => ({ ...s, smtp_password: e.target.value }))}
                placeholder={settings.smtp_password_configured ? '•••••••••••• (Configured)' : 'Enter SMTP password'}
                className="w-full text-xs font-mono text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
              />
            </div>

            {/* Sender Display Name & From Address */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 font-semibold">
                  Sender Name
                </label>
                <input
                  type="text"
                  value={settings.smtp_from_name || ''}
                  onChange={e => setSettings(s => ({ ...s, smtp_from_name: e.target.value }))}
                  placeholder="Healthcare DQ Monitor"
                  className="w-full text-xs font-sans text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 font-semibold">
                  Admin Alert Email
                </label>
                <input
                  type="email"
                  value={settings.admin_alert_email || ''}
                  onChange={e => setSettings(s => ({ ...s, admin_alert_email: e.target.value }))}
                  placeholder="admin@healthdata-ops.internal"
                  className="w-full text-xs font-sans text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
                />
              </div>
            </div>

            {/* TLS Checkbox */}
            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="tls-toggle"
                checked={settings.smtp_use_tls !== false}
                onChange={e => setSettings(s => ({ ...s, smtp_use_tls: e.target.checked }))}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="tls-toggle" className="text-xs font-medium text-slate-700">
                Enable STARTTLS Encryption (Port 587 Recommended)
              </label>
            </div>

            {/* Gmail App Password Helper Callout */}
            <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1.5">
              <p className="font-bold flex items-center gap-1.5 text-amber-950">
                <Key className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
                <span>Using Gmail / Google Workspace?</span>
              </p>
              <p className="text-[11px] leading-relaxed text-amber-900">
                Google requires an <strong>App Password</strong> (not your regular Google login password):
              </p>
              <ol className="list-decimal pl-4 text-[11px] space-y-1 text-amber-900">
                <li>Turn on <strong>2-Step Verification</strong> in your Google Account.</li>
                <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-blue-700 font-semibold underline">myaccount.google.com/apppasswords</a>.</li>
                <li>Create an App Password (name: <code className="font-mono bg-amber-100 px-1 rounded">DQ Monitor</code>).</li>
                <li>Paste the <strong>16-letter code</strong> into the <em>SMTP Password</em> box above.</li>
              </ol>
            </div>
          </div>

          {/* Test SMTP Email Dispatch Card */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs p-5 space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <Send className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-mono uppercase tracking-widest text-slate-700 font-bold">
                Live SMTP Relay Verification
              </h3>
            </div>
            <p className="text-[11px] text-slate-500">
              Dispatch a live test email to verify host connectivity, TLS handshake, and authentication.
            </p>

            <div className="space-y-2">
              <input
                type="email"
                value={testEmail}
                onChange={e => setTestEmail(e.target.value)}
                placeholder="recipient@example.com"
                className="w-full text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 outline-none focus:bg-white focus:border-blue-500"
              />
              <button
                type="button"
                onClick={handleTestEmail}
                disabled={testing || !testEmail.trim()}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-white shadow-sm transition-all disabled:opacity-50 hover:bg-emerald-700"
                style={{ background: '#059669' }}
              >
                {testing ? (
                  <><Loader2 className="w-3.5 h-3.5 animate-spin" />Testing Connection…</>
                ) : (
                  <><Send className="w-3.5 h-3.5" />Send Test Email</>
                )}
              </button>
            </div>

            {testResult && (
              <div className={`p-3 rounded-lg border text-xs font-mono mt-2 ${
                testResult.success
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-amber-50 border-amber-200 text-amber-900'
              }`}>
                <p className="font-bold flex items-center gap-1.5 mb-1">
                  {testResult.success ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <AlertCircle className="w-3.5 h-3.5 text-amber-600" />}
                  <span>{testResult.success ? 'Verification Successful' : 'Relay Notice'}</span>
                </p>
                <p className="text-[11px] leading-relaxed">{testResult.message}</p>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}

export default NotificationSettingsPage;
