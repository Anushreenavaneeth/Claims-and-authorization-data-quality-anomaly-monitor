import { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Database, 
  Clock, 
  FileText, 
  Play, 
  HelpCircle, 
  UserCheck, 
  Bell,
  Check
} from 'lucide-react';

interface Anomaly {
  id: string;
  source: string;
  metric: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'detected' | 'under_investigation' | 'remediated';
  timestamp: string;
  slaBreachTime: string;
  description: string;
  recommendation?: string;
}

const mockAnomalies: Anomaly[] = [
  {
    id: 'ANM-001',
    source: 'Claims Stream',
    metric: 'Volume Outlier',
    severity: 'critical',
    status: 'detected',
    timestamp: '2026-08-18 10:45:00',
    slaBreachTime: '45 mins remaining',
    description: 'Incoming claims volume dropped by 84% from historic baseline for Tuesdays.',
    recommendation: 'Check the claims ingest parser configuration. An schema validation exception may have stalled batch ingestion.'
  },
  {
    id: 'ANM-002',
    source: 'Pharmacy Ingestion',
    metric: 'Null Rate Spiked',
    severity: 'high',
    status: 'under_investigation',
    timestamp: '2026-08-18 10:30:00',
    slaBreachTime: '2 hours remaining',
    description: 'NPI (National Provider Identifier) field null rate rose to 42% on incoming prescription records.',
    recommendation: 'Incoming pharmacy partner "MediRx" deployed a data format change causing parser mappings to fail.'
  },
  {
    id: 'ANM-003',
    source: 'Pre-Auth Engine',
    metric: 'High Response Latency',
    severity: 'medium',
    status: 'remediated',
    timestamp: '2026-08-18 09:15:00',
    slaBreachTime: 'Remediated',
    description: 'Average pre-auth validation processing time exceeded 4.5s (SLA limit 2.0s).',
    recommendation: 'Database connection pool was saturated. Scaled connections count in pool configuration.'
  }
];

export default function App() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>(mockAnomalies);
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(mockAnomalies[0]);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [telemetryRate, setTelemetryRate] = useState(128); // claims/sec
  const [pipelineState, setPipelineState] = useState<'healthy' | 'warning' | 'error'>('warning');

  // Simulate active telemetry fluctuations
  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetryRate(prev => {
        const delta = Math.floor(Math.random() * 15) - 7;
        const next = Math.max(90, Math.min(180, prev + delta));
        return next;
      });
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const triggerDemoEvent = () => {
    setIsDemoRunning(true);
    setTimeout(() => {
      // Add a simulated synthetic anomaly
      const newAnomaly: Anomaly = {
        id: `ANM-00${anomalies.length + 1}`,
        source: 'Pre-Auth Engine',
        metric: 'Schema Drift',
        severity: 'high',
        status: 'detected',
        timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
        slaBreachTime: '1 hour remaining',
        description: 'New unsupported field "patient_consent_version" found in payload.',
        recommendation: 'Execute database schema migration standard script 104b to update Pre-Auth table structure.'
      };
      setAnomalies(prev => [newAnomaly, ...prev]);
      setSelectedAnomaly(newAnomaly);
      setPipelineState('error');
      setIsDemoRunning(false);
    }, 2000);
  };

  const updateStatus = (id: string, newStatus: Anomaly['status']) => {
    setAnomalies(prev => prev.map(a => a.id === id ? { ...a, status: newStatus } : a));
    if (selectedAnomaly && selectedAnomaly.id === id) {
      setSelectedAnomaly(prev => prev ? { ...prev, status: newStatus } : null);
    }
    // Re-check pipeline health
    setTimeout(() => {
      const activeHigh = anomalies.some(a => a.status !== 'remediated' && (a.severity === 'high' || a.severity === 'critical'));
      if (!activeHigh && newStatus === 'remediated') {
        setPipelineState('healthy');
      }
    }, 100);
  };

  const getSeverityBadge = (severity: Anomaly['severity']) => {
    const classes = {
      low: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      critical: 'bg-red-500/10 text-red-400 border-red-500/30'
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${classes[severity]}`}>
        {severity.toUpperCase()}
      </span>
    );
  };

  const getStatusBadge = (status: Anomaly['status']) => {
    const classes = {
      detected: 'bg-red-500/20 text-red-300 border-red-500/40',
      under_investigation: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
      remediated: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium border ${classes[status]}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-[#0F172A] px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg text-white">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">HDOP</h1>
            <p className="text-xs text-slate-400">Healthcare Data Operations Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Global Pipeline Health */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">System Health:</span>
            {pipelineState === 'healthy' && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                <CheckCircle className="w-3.5 h-3.5" /> ONLINE
              </span>
            )}
            {pipelineState === 'warning' && (
              <span className="flex items-center gap-1.5 text-xs text-yellow-400 font-semibold bg-yellow-500/10 px-2.5 py-1 rounded-full border border-yellow-500/20">
                <AlertTriangle className="w-3.5 h-3.5" /> DEGRADED
              </span>
            )}
            {pipelineState === 'error' && (
              <span className="flex items-center gap-1.5 text-xs text-red-400 font-semibold bg-red-500/10 px-2.5 py-1 rounded-full border border-red-500/20">
                <AlertTriangle className="w-3.5 h-3.5" /> DRIFT ALERT
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={triggerDemoEvent}
              disabled={isDemoRunning}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-95 transition-all text-sm rounded-lg font-semibold shadow-lg disabled:opacity-50"
            >
              <Play className="w-4 h-4" /> 
              {isDemoRunning ? 'Generating Anomaly...' : 'Inject Demo Anomaly'}
            </button>
            <div className="relative">
              <Bell className="w-5 h-5 text-slate-400 hover:text-white cursor-pointer" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Side: Telemetry Widgets */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">Live Pipeline Telemetry</h2>
          
          {/* Telemetry Widget 1 */}
          <div className="bg-[#161F30] border border-slate-800 rounded-xl p-5 hover-card-effect">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold text-slate-400">Overall Claims Throughput</p>
                <h3 className="text-3xl font-bold mt-1 text-white tracking-tight">{telemetryRate} <span className="text-sm font-normal text-slate-400">/ sec</span></h3>
              </div>
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
                <Database className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="inline-block w-2 h-2 bg-emerald-400 rounded-full animate-ping"></span>
              Live telemetry active
            </div>
          </div>

          {/* Telemetry Widget 2 */}
          <div className="bg-[#161F30] border border-slate-800 rounded-xl p-5 hover-card-effect">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold text-slate-400">SLA Breach Risk (ML3)</p>
                <h3 className="text-2xl font-bold mt-1 text-red-400 tracking-tight">HIGH RISK</h3>
              </div>
              <div className="p-2 bg-red-500/10 text-red-400 rounded-lg">
                <Clock className="w-5 h-5" />
              </div>
            </div>
            <p className="mt-2 text-xs text-slate-400">
              ML predicted latency: <span className="text-slate-200 font-semibold">120 mins</span>. Average threshold: 90 mins.
            </p>
          </div>

          {/* Telemetry Widget 3 */}
          <div className="bg-[#161F30] border border-slate-800 rounded-xl p-5 hover-card-effect">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-semibold text-slate-400">Pipeline Ingestion Count</p>
                <h3 className="text-2xl font-bold mt-1 text-slate-200 tracking-tight">3,492,084</h3>
              </div>
              <div className="p-2 bg-slate-500/10 text-slate-400 rounded-lg">
                <FileText className="w-5 h-5" />
              </div>
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Errors / Success ratio: <span className="text-red-400">0.08%</span> (Normal rate &lt; 0.1%)
            </p>
          </div>
        </div>

        {/* Center: Anomalies Table */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">Active Pipeline Anomalies</h2>
            <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
              {anomalies.filter(a => a.status !== 'remediated').length} Unresolved
            </span>
          </div>

          <div className="bg-[#161F30] border border-slate-800 rounded-xl overflow-hidden flex-1 flex flex-col">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#0F172A] text-slate-400 text-xs font-semibold border-b border-slate-800 uppercase">
                  <tr>
                    <th className="px-5 py-3.5">ID / Source</th>
                    <th className="px-5 py-3.5">Anomaly Type</th>
                    <th className="px-5 py-3.5">Severity</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5">SLA Deadline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {anomalies.map(anomaly => (
                    <tr 
                      key={anomaly.id}
                      onClick={() => setSelectedAnomaly(anomaly)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${selectedAnomaly?.id === anomaly.id ? 'bg-blue-600/10 border-l-2 border-blue-500' : ''}`}
                    >
                      <td className="px-5 py-4">
                        <div className="font-semibold text-slate-200">{anomaly.id}</div>
                        <div className="text-xs text-slate-400">{anomaly.source}</div>
                      </td>
                      <td className="px-5 py-4 font-medium text-slate-300">
                        {anomaly.metric}
                      </td>
                      <td className="px-5 py-4">
                        {getSeverityBadge(anomaly.severity)}
                      </td>
                      <td className="px-5 py-4">
                        {getStatusBadge(anomaly.status)}
                      </td>
                      <td className="px-5 py-4 text-xs font-semibold text-slate-300">
                        {anomaly.slaBreachTime}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Side: RAG Assistant & Details */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <h2 className="text-sm font-semibold tracking-wider text-slate-400 uppercase">Investigation Center</h2>

          {selectedAnomaly ? (
            <div className="bg-[#161F30] border border-slate-800 rounded-xl p-5 flex flex-col gap-5 flex-1 justify-between">
              <div>
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-white tracking-tight">{selectedAnomaly.id}</h3>
                    <p className="text-xs text-slate-400">{selectedAnomaly.source}</p>
                  </div>
                  {getSeverityBadge(selectedAnomaly.severity)}
                </div>

                <div className="mt-4 border-t border-slate-800 pt-4">
                  <span className="text-xs font-semibold text-slate-400">Description</span>
                  <p className="mt-1 text-sm text-slate-300 leading-relaxed">
                    {selectedAnomaly.description}
                  </p>
                </div>

                {selectedAnomaly.recommendation && (
                  <div className="mt-4 bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
                    <span className="text-xs font-semibold text-blue-400 flex items-center gap-1.5">
                      <HelpCircle className="w-3.5 h-3.5" /> AI Recommended Remediation (RAG)
                    </span>
                    <p className="mt-1 text-xs text-slate-300 leading-relaxed">
                      {selectedAnomaly.recommendation}
                    </p>
                  </div>
                )}
              </div>

              {/* Investigation Actions */}
              <div className="border-t border-slate-800 pt-4 flex flex-col gap-2 mt-4">
                <span className="text-xs font-semibold text-slate-400 mb-1">Update Status</span>
                
                {selectedAnomaly.status === 'detected' && (
                  <button 
                    onClick={() => updateStatus(selectedAnomaly.id, 'under_investigation')}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-yellow-600 hover:bg-yellow-500 transition-colors text-white font-semibold text-sm rounded-lg"
                  >
                    <UserCheck className="w-4 h-4" /> Start Investigation
                  </button>
                )}

                {selectedAnomaly.status !== 'remediated' && (
                  <button 
                    onClick={() => updateStatus(selectedAnomaly.id, 'remediated')}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-500 transition-colors text-white font-semibold text-sm rounded-lg"
                  >
                    <Check className="w-4 h-4" /> Resolve & Remediate
                  </button>
                )}

                {selectedAnomaly.status === 'remediated' && (
                  <div className="flex items-center justify-center gap-1.5 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 py-2.5 rounded-lg text-sm font-semibold">
                    <CheckCircle className="w-4 h-4" /> Issue Remediation Complete
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-[#161F30] border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center text-center flex-1 text-slate-400">
              <AlertTriangle className="w-8 h-8 mb-2 opacity-50" />
              Select an anomaly from the table to start investigating.
            </div>
          )}
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-3.5 px-6 bg-[#0B0F19] text-center text-xs text-slate-500">
        Healthcare Data Operations Platform. All data is generated synthetically for demonstration.
      </footer>
    </div>
  );
}
