import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, ShieldAlert, BarChart2, Clock, CheckCircle2, XCircle, ChevronRight, Lightbulb, Activity, Database, Send, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { Modal } from "../components/ui/Modal";
import { Button } from "../components/ui/Button";
import { getIntegratedAnomaly, createReview } from "../services/integratedApi";
import { getSeverityColor } from "../lib/utils";
import type { IntegratedRecord } from "../types/integrated";

// ── helpers ────────────────────────────────────────────────────────────────

function ScoreBar({ label, value, max = 100 }: { label: string; value: number; max?: number }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const color = pct >= 80 ? "bg-red-500" : pct >= 50 ? "bg-orange-500" : pct >= 25 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="text-xs font-medium tabular-nums">{value.toFixed(max <= 1 ? 3 : 1)}</span>
      </div>
      <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (!items.length) return <p className="text-sm text-muted-foreground">None detected.</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
          <span className="text-muted-foreground leading-relaxed">{item}</span>
        </li>
      ))}
    </ul>
  );
}

function SectionCard({ title, icon: Icon, iconColor, children }: {
  title: string; icon: React.ElementType; iconColor: string; children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className={`w-5 h-5 ${iconColor}`} />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export default function AnomalyDetailPage() {
  const { recordId } = useParams<{ recordId: string }>();
  const navigate     = useNavigate();
  const [record,       setRecord]       = useState<IntegratedRecord | null>(null);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState<string | null>(null);
  const [reviewModal,  setReviewModal]  = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewDone,   setReviewDone]   = useState(false);

  useEffect(() => {
    if (!recordId) return;
    setLoading(true);
    getIntegratedAnomaly(decodeURIComponent(recordId))
      .then(setRecord)
      .catch(e => setError(e?.response?.data?.detail ?? e.message ?? "Failed to load"))
      .finally(() => setLoading(false));
  }, [recordId]);

  const handleSendToReview = async () => {
    if (!record) return;
    setReviewSaving(true);
    try {
      await createReview({
        anomaly_record_id:       record.record_id,
        dataset:                 record.dataset,
        recommendation_snapshot: record.rag.recommendation,
      });
      setReviewDone(true);
      setReviewModal(false);
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to create review");
    } finally {
      setReviewSaving(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
    </div>
  );

  if (error || !record) return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <XCircle className="w-12 h-12 text-red-500" />
      <p className="text-muted-foreground">{error ?? "Record not found"}</p>
      <button onClick={() => navigate("/admin/anomalies")}
              className="text-sm text-blue-600 hover:underline">← Back to anomalies</button>
    </div>
  );

  const sevClass = getSeverityColor(record.anomaly.severity);

  return (
    <div className="space-y-5">

      {/* Breadcrumb */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => navigate("/admin/anomalies")}
                  className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> Anomalies
          </button>
          <span className="text-muted-foreground">/</span>
          <span className="font-mono text-foreground truncate max-w-xs">{record.record_id}</span>
        </div>
        {record.anomaly.is_anomaly && (
          <div className="flex items-center gap-2">
            {reviewDone ? (
              <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
                <CheckCircle className="w-4 h-4" /> Sent to Review
              </span>
            ) : (
              <Button size="sm" onClick={() => setReviewModal(true)}>
                <Send className="h-4 w-4 mr-2" /> Send to Review
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Overview header card */}
      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <Badge variant="info" className="capitalize">{record.dataset}</Badge>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${sevClass}`}>
                  {record.anomaly.severity}
                </span>
                <StatusBadge status={record.sla.status} />
                <StatusBadge status={record.sla.priority} type="priority" />
              </div>
              <h1 className="text-xl font-bold font-mono break-all">{record.record_id}</h1>
              <p className="text-xs text-muted-foreground mt-1">
                Processed: {new Date(record.timestamp).toLocaleString()} ·
                Status: <span className="text-green-600 font-medium">{record.processing_status}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {record.anomaly.is_anomaly
                ? <XCircle className="w-5 h-5 text-red-500" />
                : <CheckCircle2 className="w-5 h-5 text-green-500" />}
              <span className={`font-semibold text-sm ${record.anomaly.is_anomaly ? "text-red-600" : "text-green-600"}`}>
                {record.anomaly.is_anomaly ? "ANOMALY DETECTED" : "NORMAL"}
              </span>
            </div>
          </div>

          {record.anomaly.signals.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {record.anomaly.signals.map(sig => (
                <Badge key={sig} variant="info">{sig}</Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analysis grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* ML Analysis */}
        <SectionCard title="ML Analysis" icon={Activity} iconColor="text-blue-600">
          <div className="space-y-2 mb-3 text-sm">
            <div><span className="text-muted-foreground">Model: </span><span className="font-medium">{record.ml.model}</span></div>
            <div><span className="text-muted-foreground">Prediction: </span>
              <span className={`font-semibold ${record.ml.prediction === "anomaly" ? "text-red-600" : "text-green-600"}`}>
                {record.ml.prediction.toUpperCase()}
              </span>
            </div>
          </div>
          <ScoreBar label="Anomaly Score" value={record.anomaly.anomaly_score} max={1} />
          {record.ml.reasons.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Evidence</p>
              <BulletList items={record.ml.reasons} />
            </div>
          )}
        </SectionCard>

        {/* Rule Analysis */}
        <SectionCard title="Rule Analysis" icon={ShieldAlert} iconColor="text-orange-600">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-3xl font-bold">{record.rules.violation_count}</span>
            <span className="text-sm text-muted-foreground">rule violations</span>
          </div>
          {record.rules.rule_names.length > 0 ? (
            <div className="mb-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Rules Triggered</p>
              <div className="flex flex-wrap gap-2">
                {record.rules.rule_names.map(rn => (
                  <Badge key={rn} variant="warning">{rn.replace(/_/g, " ")}</Badge>
                ))}
              </div>
            </div>
          ) : <p className="text-sm text-muted-foreground mb-3">No rule violations detected.</p>}
          {record.rules.violations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Violations</p>
              <BulletList items={record.rules.violations} />
            </div>
          )}
        </SectionCard>

        {/* Bayesian Analysis */}
        <SectionCard title="Bayesian Analysis" icon={BarChart2} iconColor="text-purple-600">
          <div className="flex items-center gap-2 mb-3">
            {record.bayesian.is_anomaly
              ? <XCircle className="w-4 h-4 text-red-500" />
              : <CheckCircle2 className="w-4 h-4 text-green-500" />}
            <span className={`text-sm font-medium ${record.bayesian.is_anomaly ? "text-red-600" : "text-green-600"}`}>
              {record.bayesian.is_anomaly ? "Bayesian Anomaly" : "Bayesian Normal"}
            </span>
          </div>
          <ScoreBar label="Probability" value={record.bayesian.probability} max={1} />
          <ScoreBar label="Confidence"  value={record.bayesian.confidence}  max={1} />
          {record.bayesian.root_causes.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Root Causes</p>
              <BulletList items={record.bayesian.root_causes} />
            </div>
          )}
        </SectionCard>

        {/* Data Quality */}
        <SectionCard title="Data Quality" icon={Database} iconColor="text-green-600">
          <ScoreBar label="Quality Score" value={record.quality.quality_score} max={100} />
          <div className="mt-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Issues Detected</p>
            {record.quality.issues.length > 0
              ? <BulletList items={record.quality.issues} />
              : <p className="text-sm text-green-600 font-medium">✓ No quality issues</p>}
          </div>
          <div className="mt-4 pt-3 border-t">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Record Context</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(record.metadata)
                .filter(([k, v]) => v && k !== "context_for_rag")
                .slice(0, 8)
                .map(([k, v]) => (
                  <div key={k}>
                    <p className="text-[10px] text-muted-foreground uppercase">{k.replace(/_/g, " ")}</p>
                    <p className="text-xs font-medium truncate">{v}</p>
                  </div>
                ))}
            </div>
          </div>
        </SectionCard>
      </div>

      {/* SLA + RAG */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* SLA */}
        <SectionCard title="SLA Risk Assessment" icon={Clock} iconColor="text-red-600">
          <div className="flex items-center gap-4 mb-4">
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Risk Score</p>
              <p className="text-3xl font-bold">{record.sla.risk_score.toFixed(1)}</p>
            </div>
            <div className="flex flex-col gap-2">
              <StatusBadge status={record.sla.risk_level} />
              <StatusBadge status={record.sla.priority} type="priority" />
              <StatusBadge status={record.sla.status} />
            </div>
          </div>
          <ScoreBar label="Risk Score" value={record.sla.risk_score} max={100} />
          <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">Response Time</p>
              <p className="font-medium">{record.sla.response_time}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Escalation</p>
              <p className={`font-medium ${record.sla.escalation_required ? "text-red-600" : "text-green-600"}`}>
                {record.sla.escalation_required ? "⚠ Required" : "✓ Not required"}
              </p>
            </div>
          </div>
          <div className="mt-3 p-3 bg-gray-50 border rounded-lg">
            <p className="text-xs text-muted-foreground mb-1 font-medium">{record.sla.action}</p>
            <p className="text-sm text-muted-foreground">{record.sla.recommendation}</p>
          </div>
        </SectionCard>

        {/* RAG Recommendation */}
        <SectionCard title="AI Recommendation" icon={Lightbulb} iconColor="text-yellow-600">
          <div className="flex items-center justify-between mb-3">
            <Badge variant="success">{(record.rag.confidence * 100).toFixed(0)}% confidence</Badge>
            <StatusBadge status={record.rag.priority} type="priority" />
          </div>

          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg mb-3">
            <p className="text-xs font-medium text-yellow-800 mb-1 uppercase tracking-wide">Recommendation</p>
            <p className="text-sm">{record.rag.recommendation}</p>
          </div>

          {record.rag.explanation && (
            <div className="mb-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Why Flagged</p>
              <p className="text-sm text-muted-foreground">{record.rag.explanation}</p>
            </div>
          )}

          {record.rag.root_cause && (
            <div className="mb-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Root Cause</p>
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm">{record.rag.root_cause}</p>
              </div>
            </div>
          )}

          {record.rag.recommended_actions.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Recommended Actions</p>
              <ol className="space-y-2">
                {record.rag.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-muted-foreground leading-relaxed">{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {record.rag.evidence.length > 0 && (
            <div className="mt-3 pt-3 border-t">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Supporting Evidence</p>
              <BulletList items={record.rag.evidence.slice(0, 3)} />
            </div>
          )}
        </SectionCard>
      </div>

      {/* Processing errors */}
      {record.processing_errors.length > 0 && (
        <Card className="border-red-200">
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-red-600 uppercase mb-2">Processing Warnings</p>
            <BulletList items={record.processing_errors} />
          </CardContent>
        </Card>
      )}

      {/* Send to Review confirmation modal */}
      <Modal isOpen={reviewModal} onClose={() => setReviewModal(false)} title="Send to Human Review">
        <div className="space-y-4">
          <p className="text-sm">
            This will create a review entry for <span className="font-mono font-medium">{record.record_id}</span>.
            A reviewer can then approve, reject, or modify the recommendation before any action is taken.
          </p>
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm">
            <p className="font-medium text-yellow-800 mb-1">Recommendation to review:</p>
            <p className="text-yellow-900 line-clamp-3">{record.rag.recommendation}</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleSendToReview} disabled={reviewSaving}>
              <Send className="h-4 w-4 mr-2" />
              {reviewSaving ? "Sending…" : "Confirm — Send to Review"}
            </Button>
            <Button variant="outline" onClick={() => setReviewModal(false)}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
