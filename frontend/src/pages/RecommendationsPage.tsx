import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { getIntegratedAnomalies, getRootCauses } from "../services/integratedApi";
import { formatNumber } from "../lib/utils";
import { Lightbulb, BookOpen, Search, TrendingUp, AlertTriangle } from "lucide-react";
import type { IntegratedRecord } from "../types/integrated";

export function RecommendationsPage() {
  const [records,    setRecords]    = useState<IntegratedRecord[]>([]);
  const [rootCauses, setRootCauses] = useState<{ rule: string; count: number }[]>([]);
  const [selected,   setSelected]   = useState<IntegratedRecord | null>(null);
  const [search,     setSearch]     = useState("");
  const [loading,    setLoading]    = useState(true);

  useEffect(() => {
    Promise.all([
      getIntegratedAnomalies({ is_anomaly: true, page_size: 100 }),
      getRootCauses(),
    ]).then(([r, rc]) => {
      setRecords(r.items);
      setRootCauses(rc.root_causes ?? []);
    }).finally(() => setLoading(false));
  }, []);

  const filtered = records.filter(r =>
    !search ||
    r.record_id.toLowerCase().includes(search.toLowerCase()) ||
    r.rag.recommendation.toLowerCase().includes(search.toLowerCase())
  );

  const highConf    = records.filter(r => r.rag.confidence >= 0.8).length;
  const avgConf     = records.length > 0
    ? records.reduce((s, r) => s + r.rag.confidence, 0) / records.length : 0;

  if (loading) return <div className="flex items-center justify-center h-64 text-muted-foreground">Loading recommendations…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Recommended Actions (RAG)</h1>
        <p className="text-muted-foreground mt-1">AI-generated recommendations for detected anomalies</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Total Recommendations</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{formatNumber(records.length)}</div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">High Confidence (≥80%)</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-600">{highConf}</div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Avg Confidence</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{(avgConf * 100).toFixed(0)}%</div></CardContent></Card>
        <Card><CardHeader className="pb-3"><CardTitle className="text-sm font-medium text-muted-foreground">Root Cause Types</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold">{rootCauses.length}</div></CardContent></Card>
      </div>

      {/* Recommendation Cards */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5" />Recommendations</CardTitle>
          <CardDescription>Click any record to view the full AI recommendation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search recommendations…" className="pl-10"
                     value={search} onChange={e => setSearch(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto">
            {filtered.slice(0, 50).map(r => (
              <div key={r.record_id}
                   className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                   onClick={() => setSelected(r)}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <p className="font-medium text-xs font-mono truncate">{r.record_id}</p>
                    <p className="text-xs text-muted-foreground capitalize mt-0.5">{r.dataset}</p>
                  </div>
                  <div className="flex flex-col gap-1 ml-2">
                    <Badge variant="success">{(r.rag.confidence * 100).toFixed(0)}% conf</Badge>
                    <Badge variant={r.sla.risk_level === "CRITICAL" ? "error" : r.sla.risk_level === "HIGH" ? "warning" : "info"}>
                      {r.sla.priority}
                    </Badge>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2 mt-1">{r.rag.recommendation}</p>
                {r.rag.recommended_actions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium mb-1">Actions:</p>
                    <ol className="list-decimal list-inside text-xs text-muted-foreground space-y-0.5">
                      {r.rag.recommended_actions.slice(0, 2).map((a, i) => (
                        <li key={i} className="truncate">{a}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Root Causes Knowledge Base */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><BookOpen className="h-5 w-5" />Top Root Causes</CardTitle>
          <CardDescription>Most frequently detected rule violations across all datasets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rootCauses.slice(0, 12).map(rc => (
              <div key={rc.rule} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-sm">{rc.rule.replace(/_/g, " ")}</h4>
                  <Badge variant="warning">{rc.count}</Badge>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <TrendingUp className="h-3 w-3" />
                  <span className="text-xs">Referenced {rc.count} times</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selected && (
        <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="AI Recommendation" size="lg">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge variant="info" className="capitalize">{selected.dataset}</Badge>
              <Badge variant={selected.sla.risk_level === "CRITICAL" ? "error" : "warning"}>
                {selected.sla.priority} · {selected.sla.risk_level}
              </Badge>
              <Badge variant="success">{(selected.rag.confidence * 100).toFixed(0)}% confidence</Badge>
            </div>
            <p className="font-mono text-xs text-muted-foreground">{selected.record_id}</p>

            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 mb-1">Recommendation</p>
              <p className="text-sm">{selected.rag.recommendation}</p>
            </div>

            {selected.rag.explanation && (
              <div>
                <h4 className="font-semibold text-sm mb-1 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />Why Was This Flagged
                </h4>
                <p className="text-sm text-muted-foreground">{selected.rag.explanation}</p>
              </div>
            )}

            {selected.rag.root_cause && (
              <div>
                <h4 className="font-semibold text-sm mb-1">Root Cause</h4>
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm">{selected.rag.root_cause}</p>
                </div>
              </div>
            )}

            {selected.rag.recommended_actions.length > 0 && (
              <div>
                <h4 className="font-semibold text-sm mb-2">Recommended Actions</h4>
                <ol className="list-decimal list-inside text-sm space-y-1.5 text-muted-foreground">
                  {selected.rag.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}
                </ol>
              </div>
            )}

            {selected.sla.escalation_required && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700 font-medium">
                  ⚠ Escalation Required — Response within {selected.sla.response_time}
                </p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
