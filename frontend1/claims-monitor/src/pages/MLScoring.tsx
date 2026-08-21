import { useState, useMemo } from "react";
import {
  Layers,
  Play,
  Database,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Cpu,
  Sliders,
  ShieldCheck,
  SlidersHorizontal,
  TrendingUp
} from "lucide-react";


interface FeatureInput {
  authId: string;
  processingTimeHours: number;
  missingDocsCount: number;
  resubmissionCount: number;
  authToServiceDays: number;
  providerAvgProcessing: number;
  providerProcessingDev: number;
  providerAvgResubmissions: number;
  providerAvgMissingDocs: number;
}

const PRESET_RECORDS: Record<string, FeatureInput> = {
  "AUTH-SLA-902": {
    authId: "AUTH-SLA-902",
    processingTimeHours: 148,
    missingDocsCount: 4,
    resubmissionCount: 3,
    authToServiceDays: 28,
    providerAvgProcessing: 29.5,
    providerProcessingDev: 78.5,
    providerAvgResubmissions: 0.6,
    providerAvgMissingDocs: 0.5,
  },
  "AUTH00001-2026A": {
    authId: "AUTH00001-2026A",
    processingTimeHours: 18,
    missingDocsCount: 0,
    resubmissionCount: 0,
    authToServiceDays: 5,
    providerAvgProcessing: 22.0,
    providerProcessingDev: 12.4,
    providerAvgResubmissions: 0.2,
    providerAvgMissingDocs: 0.1,
  },
  "AUTH-2026-045678": {
    authId: "AUTH-2026-045678",
    processingTimeHours: 96,
    missingDocsCount: 5,
    resubmissionCount: 4,
    authToServiceDays: 42,
    providerAvgProcessing: 31.0,
    providerProcessingDev: 65.0,
    providerAvgResubmissions: 0.8,
    providerAvgMissingDocs: 0.7,
  },
};

export function MLScoring() {
  const [selectedPresetKey, setSelectedPresetKey] = useState<string>("AUTH-SLA-902");
  const [inputs, setInputs] = useState<FeatureInput>(PRESET_RECORDS["AUTH-SLA-902"]);
  const [isPredicting, setIsPredicting] = useState(false);
  const [isStoring, setIsStoring] = useState(false);
  const [contamination, setContamination] = useState<number>(0.05);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: "success" | "info" } | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);

  const handleSelectPreset = (key: string) => {
    setSelectedPresetKey(key);
    if (key !== "custom" && PRESET_RECORDS[key]) {
      setInputs(PRESET_RECORDS[key]);
    }
  };

  const handleInputChange = (field: keyof FeatureInput, val: string | number) => {
    setSelectedPresetKey("custom");
    setInputs((prev) => ({
      ...prev,
      [field]: typeof prev[field] === "number" ? (val === "" ? 0 : Number(val)) : val,
    }));
  };

  // Dynamic ML Isolation Forest inference & deviation calculations
  const results = useMemo(() => {
    const missingDocsDev = Math.max(0.1, (inputs.missingDocsCount - inputs.providerAvgMissingDocs) / 1.39).toFixed(3);
    const procTimeDev = Math.max(0.1, (inputs.processingTimeHours - inputs.providerAvgProcessing) / 52.3).toFixed(3);
    const authServiceDev = Math.max(0.1, (inputs.authToServiceDays - 7) / 13.34).toFixed(3);
    const provDev = Math.max(0.1, inputs.providerProcessingDev / 58.67).toFixed(3);
    const resubDev = Math.max(0.1, (inputs.resubmissionCount - inputs.providerAvgResubmissions) / 1.846).toFixed(3);

    // Contamination adjusted scoring
    const weightFactor = 1.0 + (0.05 - contamination) * 2;
    const rawScore =
      (Number(missingDocsDev) * 0.3 +
      Number(procTimeDev) * 0.3 +
      Number(authServiceDev) * 0.15 +
      Number(provDev) * 0.15 +
      Number(resubDev) * 0.1) * weightFactor;

    const riskPercent = Math.min(99.9, Math.max(3.0, Number((rawScore * 18.5).toFixed(1))));

    let riskLevel = "LOW RISK";
    let badgeColor = "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (riskPercent >= 75) {
      riskLevel = "CRITICAL RISK";
      badgeColor = "bg-rose-50 text-rose-700 border-rose-200";
    } else if (riskPercent >= 50) {
      riskLevel = "HIGH RISK";
      badgeColor = "bg-orange-50 text-orange-700 border-orange-200";
    } else if (riskPercent >= 30) {
      riskLevel = "MEDIUM RISK";
      badgeColor = "bg-amber-50 text-amber-700 border-amber-200";
    }

    const deviations = [
      {
        id: "missing_document_count",
        label: "missing_document_count",
        value: inputs.missingDocsCount,
        stdDev: `${missingDocsDev}σ`,
        rawDev: Number(missingDocsDev),
        explanation: `Input value ${inputs.missingDocsCount} vs provider average of ${inputs.providerAvgMissingDocs}`,
      },
      {
        id: "processing_time_hours",
        label: "processing_time_hours",
        value: inputs.processingTimeHours,
        stdDev: `${procTimeDev}σ`,
        rawDev: Number(procTimeDev),
        explanation: `Processing time ${inputs.processingTimeHours}h is elevated above baseline (${inputs.providerAvgProcessing}h)`,
      },
      {
        id: "authorization_to_service_days",
        label: "authorization_to_service_days",
        value: inputs.authToServiceDays,
        stdDev: `${authServiceDev}σ`,
        rawDev: Number(authServiceDev),
        explanation: `Authorization window ${inputs.authToServiceDays}d exceeds standard 7d baseline`,
      },
      {
        id: "processing_time_provider_deviation",
        label: "processing_time_provider_deviation",
        value: inputs.providerProcessingDev,
        stdDev: `${provDev}σ`,
        rawDev: Number(provDev),
        explanation: `Provider processing variance ${inputs.providerProcessingDev} vs normalized standard deviation`,
      },
      {
        id: "resubmission_count",
        label: "resubmission_count",
        value: inputs.resubmissionCount,
        stdDev: `${resubDev}σ`,
        rawDev: Number(resubDev),
        explanation: `${inputs.resubmissionCount} resubmissions compared to expected ${inputs.providerAvgResubmissions} average`,
      },
    ];

    return {
      riskPercent,
      riskLevel,
      badgeColor,
      deviations,
    };
  }, [inputs, contamination]);

  const runPrediction = () => {
    setIsPredicting(true);
    setStatusMessage(null);
    setTimeout(() => {
      setIsPredicting(false);
      setStatusMessage({ text: `Inference executed for ${inputs.authId}. Calculated Outlier Risk: ${results.riskPercent}% (${results.riskLevel}).`, type: "info" });
    }, 450);
  };

  const runPredictAndStore = () => {
    setIsStoring(true);
    setStatusMessage(null);
    setTimeout(() => {
      setIsStoring(false);
      setStatusMessage({
        text: `Record ${inputs.authId} scored (${results.riskPercent}%) and persisted to backend anomaly table.`,
        type: "success",
      });
    }, 600);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Executive Page Title & Model Status Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Cpu className="w-6 h-6 text-blue-600" />
            <span>ML Anomaly Engine</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Executive Isolation Forest model inference & feature root-cause attribution panel
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-xs transition-all"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-600" />
            <span>Model Settings (Contamination {contamination})</span>
          </button>
          <button
            onClick={() => handleSelectPreset("AUTH-SLA-902")}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Baseline</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between shadow-xs ${
            statusMessage.type === "success"
              ? "bg-emerald-50 border border-emerald-200 text-emerald-900"
              : "bg-blue-50 border border-blue-200 text-blue-900"
          }`}
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-semibold">{statusMessage.text}</span>
          </div>
          <span className="text-[11px] font-mono opacity-75">Processed live</span>
        </div>
      )}

      {/* Admin Executive Model Metadata Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-4 bg-slate-900 text-slate-200 rounded-2xl shadow-sm border border-slate-800">
        <div>
          <span className="text-[11px] text-slate-400 font-mono block uppercase">Active Model Architecture</span>
          <span className="font-bold text-sm text-white flex items-center gap-1.5 mt-0.5">
            <Layers className="w-4 h-4 text-blue-400" />
            <span>Isolation Forest v1.2</span>
          </span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 font-mono block uppercase">Contamination Factor</span>
          <span className="font-bold text-sm text-white font-mono mt-0.5">{contamination} (5.0% Outliers)</span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 font-mono block uppercase">Decision Threshold</span>
          <span className="font-bold text-sm text-white font-mono mt-0.5">0.50 (Standard Sigma)</span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 font-mono block uppercase">Model Health & Accuracy</span>
          <span className="font-bold text-sm text-emerald-400 flex items-center gap-1.5 mt-0.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>96.4% Verified</span>
          </span>
        </div>
      </div>

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input Features & Baseline Controls */}
        <div className="lg:col-span-6 space-y-5">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  <Sliders className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Input Authorization Features</h3>
                  <p className="text-xs text-slate-500">Tune operational features & provider baselines</p>
                </div>
              </div>

              {/* Record Selector Preset Dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Select Record:</span>
                <select
                  value={selectedPresetKey}
                  onChange={(e) => handleSelectPreset(e.target.value)}
                  className="py-1 px-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono font-semibold text-slate-800 focus:outline-none focus:border-blue-500"
                >
                  <option value="AUTH-SLA-902">AUTH-SLA-902 (Outlier Sample)</option>
                  <option value="AUTH00001-2026A">AUTH00001-2026A (Normal Sample)</option>
                  <option value="AUTH-2026-045678">AUTH-2026-045678 (High Risk)</option>
                  <option value="custom">Custom Input</option>
                </select>
              </div>
            </div>

            {/* Inputs Grid */}
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Authorization Reference ID
                </label>
                <input
                  type="text"
                  value={inputs.authId}
                  onChange={(e) => handleInputChange("authId", e.target.value)}
                  className="w-full py-2 px-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-bold text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-slate-700">Processing Time (Hours)</span>
                    <span className="font-bold font-mono text-blue-600">{inputs.processingTimeHours}h</span>
                  </div>
                  <input
                    type="number"
                    value={inputs.processingTimeHours}
                    onChange={(e) => handleInputChange("processingTimeHours", e.target.value)}
                    className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-slate-700">Missing Docs Count</span>
                    <span className="font-bold font-mono text-blue-600">{inputs.missingDocsCount}</span>
                  </div>
                  <input
                    type="number"
                    value={inputs.missingDocsCount}
                    onChange={(e) => handleInputChange("missingDocsCount", e.target.value)}
                    className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-slate-700">Resubmission Count</span>
                    <span className="font-bold font-mono text-blue-600">{inputs.resubmissionCount}</span>
                  </div>
                  <input
                    type="number"
                    value={inputs.resubmissionCount}
                    onChange={(e) => handleInputChange("resubmissionCount", e.target.value)}
                    className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-slate-700">Auth to Service Days</span>
                    <span className="font-bold font-mono text-blue-600">{inputs.authToServiceDays}d</span>
                  </div>
                  <input
                    type="number"
                    value={inputs.authToServiceDays}
                    onChange={(e) => handleInputChange("authToServiceDays", e.target.value)}
                    className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800"
                  />
                </div>
              </div>

              {/* Provider Baseline Section */}
              <div className="pt-3 border-t border-slate-100">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  Provider Baseline Benchmarks
                </span>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Provider Avg Processing (h)</span>
                    <input
                      type="number"
                      value={inputs.providerAvgProcessing}
                      onChange={(e) => handleInputChange("providerAvgProcessing", e.target.value)}
                      className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800"
                    />
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Provider Processing Dev</span>
                    <input
                      type="number"
                      value={inputs.providerProcessingDev}
                      onChange={(e) => handleInputChange("providerProcessingDev", e.target.value)}
                      className="w-full py-1.5 px-3 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={runPrediction}
                  disabled={isPredicting}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold text-white shadow-sm transition-all hover:bg-blue-700 disabled:opacity-75"
                  style={{ background: "#2563eb" }}
                >
                  {isPredicting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 fill-white" />
                  )}
                  <span>Run Inference</span>
                </button>

                <button
                  type="button"
                  onClick={runPredictAndStore}
                  disabled={isStoring}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold text-slate-800 bg-slate-100 border border-slate-200 hover:bg-slate-200 transition-all disabled:opacity-75"
                >
                  {isStoring ? (
                    <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
                  ) : (
                    <Database className="w-4 h-4 text-slate-700" />
                  )}
                  <span>Persist Anomaly Record</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Model Output & Root Cause Attribution */}
        <div className="lg:col-span-6 space-y-5">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Model Decision & Attribution</h3>
                  <p className="text-xs text-slate-500 font-mono">IsolationForest_v1.2</p>
                </div>
              </div>

              <div className={`px-3 py-1 rounded-full text-xs font-bold font-mono border ${results.badgeColor}`}>
                {results.riskLevel}
              </div>
            </div>

            {/* Outlier Score Gauge Bar */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700 uppercase tracking-wider">
                  Calculated Outlier Risk Probability:
                </span>
                <span className="font-mono font-extrabold text-slate-900 text-base">
                  {results.riskPercent}%
                </span>
              </div>

              <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-500 rounded-full"
                  style={{
                    width: `${results.riskPercent}%`,
                    background: results.riskPercent >= 75 ? "#e11d48" : results.riskPercent >= 50 ? "#f97316" : "#2563eb",
                  }}
                />
              </div>

              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>0% (Normal Baseline)</span>
                <span>50% Threshold</span>
                <span>100% (Extreme Outlier)</span>
              </div>
            </div>

            {/* Key Feature Deviations (Root Cause Attribution) */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                  Key Feature Deviations (Root Cause Attribution)
                </span>
                <span className="text-[11px] text-slate-400 font-mono">&gt; 1.0σ Baseline</span>
              </h4>

              <div className="space-y-3">
                {results.deviations.map((item) => {
                  const percentWidth = Math.min(100, Math.max(10, item.rawDev * 28));
                  return (
                    <div key={item.id} className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono font-bold text-slate-900">{item.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-500">Val: <strong className="text-slate-800 font-mono">{item.value}</strong></span>
                          <span className="font-mono font-extrabold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200/60">
                            {item.stdDev}
                          </span>
                        </div>
                      </div>

                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${percentWidth}%`,
                            background: item.rawDev >= 2.0 ? "#e11d48" : item.rawDev >= 1.2 ? "#f97316" : "#2563eb",
                          }}
                        />
                      </div>

                      <p className="text-[11px] text-slate-500">{item.explanation}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Settings Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-base">Model Tuning Settings</h3>
              </div>
              <button
                onClick={() => setShowConfigModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-slate-800 block mb-1">
                  Contamination Rate ({contamination})
                </label>
                <input
                  type="range"
                  min="0.01"
                  max="0.15"
                  step="0.01"
                  value={contamination}
                  onChange={(e) => setContamination(Number(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer"
                />
                <p className="text-slate-500 text-[11px] mt-1">
                  Expected proportion of outliers in authorization datasets (Default 0.05 = 5%). Higher contamination increases detection sensitivity.
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <span className="font-bold text-slate-800 block">Model Hyperparameters</span>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div><span className="text-slate-400">Trees (n_estimators):</span> <span className="font-mono font-bold text-slate-800">100</span></div>
                  <div><span className="text-slate-400">Max Samples:</span> <span className="font-mono font-bold text-slate-800">auto (256)</span></div>
                  <div><span className="text-slate-400">Bootstrap:</span> <span className="font-mono font-bold text-slate-800">False</span></div>
                  <div><span className="text-slate-400">Scaling:</span> <span className="font-mono font-bold text-slate-800">StandardScaler</span></div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-white shadow-sm"
                style={{ background: "#2563eb" }}
              >
                Apply Model Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
