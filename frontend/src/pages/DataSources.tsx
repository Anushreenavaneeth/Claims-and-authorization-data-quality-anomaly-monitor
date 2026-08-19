import { useState, useRef } from 'react';
import DashboardShell from '../components/DashboardShell';
import api from '../services/api';
import {
  Upload, FileText, CheckCircle2, AlertCircle,
  Loader2, ChevronDown, ChevronUp, Database,
} from 'lucide-react';

type SourceType = 'CLAIMS' | 'PHARMACY' | 'AUTHORIZATION';
type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

interface Issue {
  type: string;
  severity: string;
  column?: string;
  rows?: number;
  message: string;
}

interface UploadResult {
  upload_id:         string;
  filename:          string;
  source_type:       string;
  total_records:     number;
  valid_records:     number;
  invalid_records:   number;
  status:            string;
  issues:            Issue[];
  anomalies_created: number;
  timestamp:         string;
}

const SOURCE_OPTIONS: { value: SourceType; label: string; desc: string; color: string }[] = [
  { value: 'CLAIMS',        label: 'Claims',        desc: 'Insurance claims data',         color: '#60a5fa' },
  { value: 'PHARMACY',      label: 'Pharmacy',       desc: 'Prescription / drug data',      color: '#a78bfa' },
  { value: 'AUTHORIZATION', label: 'Authorization',  desc: 'Pre-auth / approval records',   color: '#34d399' },
];

export default function DataSources() {
  const [sourceType, setSourceType] = useState<SourceType>('CLAIMS');
  const [status,     setStatus]     = useState<UploadStatus>('idle');
  const [result,     setResult]     = useState<UploadResult | null>(null);
  const [errorMsg,   setErrorMsg]   = useState('');
  const [showIssues, setShowIssues] = useState(false);
  const [dragOver,   setDragOver]   = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = async (file: File) => {
    setStatus('uploading');
    setResult(null);
    setErrorMsg('');

    const form = new FormData();
    form.append('file', file);
    form.append('source_type', sourceType);

    try {
      const res = await api.post('/datasets/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      setStatus('success');
      setShowIssues(res.data.issues.length > 0);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setErrorMsg(typeof detail === 'string' ? detail : 'Upload failed. Try again.');
      setStatus('error');
    }
  };

  const handleFile = (file: File | null) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setErrorMsg('Only .csv files are supported.');
      setStatus('error');
      return;
    }
    upload(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0] ?? null);
  };

  const src = SOURCE_OPTIONS.find(s => s.value === sourceType)!;

  return (
    <DashboardShell>
      <div className="max-w-2xl">
        <p className="text-[10px] font-mono tracking-widest text-slate-600 uppercase mb-1">
          Admin · Data Sources
        </p>
        <h1 className="font-display text-2xl font-bold text-white mb-6">Upload Dataset</h1>

        {/* Source type selector */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          {SOURCE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setSourceType(opt.value)}
              className="rounded-xl p-3 text-left transition-all"
              style={
                sourceType === opt.value
                  ? { background: `${opt.color}15`, border: `1px solid ${opt.color}50` }
                  : { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }
              }
            >
              <p className="text-xs font-semibold text-white mb-0.5">{opt.label}</p>
              <p className="text-[10px] font-mono text-slate-500">{opt.desc}</p>
            </button>
          ))}
        </div>

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className="rounded-xl cursor-pointer transition-all mb-4"
          style={{
            border: dragOver
              ? `2px dashed ${src.color}`
              : '2px dashed rgba(255,255,255,0.08)',
            background: dragOver
              ? `${src.color}08`
              : 'rgba(255,255,255,0.02)',
            padding: '40px 24px',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={e => handleFile(e.target.files?.[0] ?? null)}
          />
          <div className="flex flex-col items-center gap-3 text-center">
            {status === 'uploading' ? (
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            ) : (
              <div className="w-12 h-12 rounded-xl flex items-center justify-center"
                   style={{ background: `${src.color}12`, border: `1px solid ${src.color}30` }}>
                <Upload className="w-5 h-5" style={{ color: src.color }} />
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-slate-200">
                {status === 'uploading' ? 'Validating…' : 'Drop CSV here or click to browse'}
              </p>
              <p className="text-[11px] font-mono text-slate-600 mt-0.5">
                {src.label} · CSV only · validated against schema
              </p>
            </div>
          </div>
        </div>

        {/* Error */}
        {status === 'error' && (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg mb-4 text-sm font-mono text-red-400"
               style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
               role="alert">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            {errorMsg}
          </div>
        )}

        {/* Result card */}
        {status === 'success' && result && (
          <div className="rounded-xl overflow-hidden"
               style={{ background: 'rgba(6,14,28,0.8)', border: '1px solid rgba(255,255,255,0.07)' }}>
            {/* Header */}
            <div className="px-5 py-4 flex items-center gap-3"
                 style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">{result.filename}</p>
                <p className="text-[10px] font-mono text-slate-500">{result.source_type} · {result.timestamp.slice(0, 19).replace('T', ' ')} UTC</p>
              </div>
              <span
                className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-full"
                style={result.status === 'PASS'
                  ? { background: 'rgba(34,197,94,0.1)', color: '#4ade80', border: '1px solid rgba(34,197,94,0.2)' }
                  : { background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}
              >
                {result.status}
              </span>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-4 divide-x"
                 style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', divideBorderColor: 'rgba(255,255,255,0.06)' }}>
              {[
                { label: 'Total',    value: result.total_records,   color: '#94a3b8' },
                { label: 'Valid',    value: result.valid_records,    color: '#4ade80' },
                { label: 'Invalid',  value: result.invalid_records,  color: result.invalid_records > 0 ? '#f87171' : '#4ade80' },
                { label: 'Anomalies', value: result.anomalies_created, color: result.anomalies_created > 0 ? '#fb923c' : '#94a3b8' },
              ].map(s => (
                <div key={s.label} className="px-4 py-3 text-center">
                  <p className="font-display text-xl font-bold" style={{ color: s.color }}>{s.value}</p>
                  <p className="text-[9px] font-mono text-slate-600 uppercase tracking-wider">{s.label}</p>
                </div>
              ))}
            </div>

            {/* Anomaly banner */}
            {result.anomalies_created > 0 && (
              <div className="px-5 py-3 flex items-center gap-2 text-xs font-mono"
                   style={{ background: 'rgba(251,146,60,0.06)', borderBottom: '1px solid rgba(251,146,60,0.12)' }}>
                <CheckCircle2 className="w-3.5 h-3.5 text-orange-400" />
                <span className="text-orange-300">
                  {result.anomalies_created} anomaly record{result.anomalies_created > 1 ? 's' : ''} created and broadcast to the live feed.
                </span>
              </div>
            )}

            {/* Issues toggle */}
            {result.issues.length > 0 && (
              <div>
                <button
                  onClick={() => setShowIssues(s => !s)}
                  className="w-full flex items-center justify-between px-5 py-3 text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <span>{result.issues.length} validation issue{result.issues.length > 1 ? 's' : ''}</span>
                  {showIssues ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
                {showIssues && (
                  <div className="px-5 pb-4 space-y-1.5"
                       style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    {result.issues.map((iss, i) => (
                      <div key={i} className="flex items-start gap-2.5 text-xs font-mono py-1">
                        <span
                          className="text-[9px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 mt-0.5"
                          style={iss.severity === 'ERROR'
                            ? { background: 'rgba(239,68,68,0.12)', color: '#f87171' }
                            : { background: 'rgba(251,146,60,0.12)', color: '#fb923c' }}
                        >
                          {iss.severity}
                        </span>
                        <span className="text-slate-400">
                          {iss.column && <span className="text-blue-400">{iss.column}: </span>}
                          {iss.message}
                          {iss.rows != null && <span className="text-slate-600"> ({iss.rows} rows)</span>}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Upload another */}
        {status === 'success' && (
          <button
            onClick={() => { setStatus('idle'); setResult(null); if (inputRef.current) inputRef.current.value = ''; }}
            className="mt-4 text-xs font-mono text-slate-600 hover:text-slate-400 transition-colors flex items-center gap-1.5"
          >
            <Database className="w-3 h-3" /> Upload another file
          </button>
        )}
      </div>
    </DashboardShell>
  );
}
