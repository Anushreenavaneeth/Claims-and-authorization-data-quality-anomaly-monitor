import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import {
  getReviews, approveReview, rejectReview, modifyReview, createReview,
  type ReviewRecord,
} from "../services/integratedApi";
import { formatDate } from "../lib/utils";
import { CheckCircle, XCircle, Edit3, AlertTriangle, Plus, RefreshCw } from "lucide-react";

type ModalType = "approve" | "reject" | "modify" | "create" | null;

export function ReviewPage() {
  const [reviews,  setReviews]  = useState<ReviewRecord[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [selected, setSelected] = useState<ReviewRecord | null>(null);
  const [modal,    setModal]    = useState<ModalType>(null);
  const [comment,  setComment]  = useState("");
  const [modText,  setModText]  = useState("");
  const [saving,   setSaving]   = useState(false);
  const [filterStatus, setFilterStatus] = useState("");

  // For creating a new review from an anomaly
  const [createRecordId, setCreateRecordId] = useState("");
  const [createDataset,  setCreateDataset]  = useState("claims");
  const [createSnapshot, setCreateSnapshot] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await getReviews({ status: filterStatus || undefined, page_size: 100 });
      setReviews(data);
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [filterStatus]);

  const closeModal = () => { setModal(null); setSelected(null); setComment(""); setModText(""); };

  const handleApprove = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await approveReview(selected.id, comment || undefined);
      await load();
      closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const handleReject = async () => {
    if (!selected || !comment.trim()) return;
    setSaving(true);
    try {
      await rejectReview(selected.id, comment);
      await load();
      closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const handleModify = async () => {
    if (!selected || !modText.trim()) return;
    setSaving(true);
    try {
      await modifyReview(selected.id, modText, comment || undefined);
      await load();
      closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const handleCreate = async () => {
    if (!createRecordId.trim()) return;
    setSaving(true);
    try {
      await createReview({
        anomaly_record_id: createRecordId,
        dataset: createDataset,
        recommendation_snapshot: createSnapshot || undefined,
      });
      await load();
      setModal(null);
      setCreateRecordId(""); setCreateDataset("claims"); setCreateSnapshot("");
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const pending   = reviews.filter(r => r.status === "pending_review");
  const approved  = reviews.filter(r => r.status === "approved");
  const rejected  = reviews.filter(r => r.status === "rejected");
  const modified  = reviews.filter(r => r.status === "modified");

  const statusVariant = (s: string) => {
    if (s === "approved")  return "success" as const;
    if (s === "rejected")  return "error"   as const;
    if (s === "modified")  return "warning" as const;
    return "info" as const;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Human Review Queue</h1>
          <p className="text-muted-foreground mt-1">
            Review anomaly recommendations before any action is executed
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button size="sm" onClick={() => setModal("create")}>
            <Plus className="h-4 w-4 mr-2" />New Review
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />{error}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Pending Review", value: pending.length,  color: "text-orange-600" },
          { label: "Approved",       value: approved.length, color: "text-green-600"  },
          { label: "Rejected",       value: rejected.length, color: "text-red-600"    },
          { label: "Modified",       value: modified.length, color: "text-blue-600"   },
        ].map(s => (
          <Card key={s.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{s.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium">Filter:</span>
        {[
          { v: "",               l: "All"     },
          { v: "pending_review", l: "Pending" },
          { v: "approved",       l: "Approved"},
          { v: "rejected",       l: "Rejected"},
          { v: "modified",       l: "Modified"},
        ].map(f => (
          <button key={f.v} onClick={() => setFilterStatus(f.v)}
                  className={`px-3 py-1 rounded-md text-sm transition-colors ${
                    filterStatus === f.v
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary hover:bg-secondary/80"
                  }`}>
            {f.l}
          </button>
        ))}
      </div>

      {/* Pending review items — action buttons visible */}
      {(!filterStatus || filterStatus === "pending_review") && pending.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-600">
              <AlertTriangle className="h-5 w-5" />
              Pending Review ({pending.length})
            </CardTitle>
            <CardDescription>These recommendations require your decision before an action can be created</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {pending.map(r => (
              <div key={r.id} className="p-4 border rounded-lg space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-mono text-sm font-medium truncate">{r.anomaly_record_id}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="info" className="capitalize">{r.dataset}</Badge>
                      <span className="text-xs text-muted-foreground">{formatDate(r.created_at)}</span>
                    </div>
                  </div>
                  <Badge variant={statusVariant(r.status)}>{r.status.replace("_", " ")}</Badge>
                </div>

                {r.recommendation_snapshot && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm">
                    <p className="text-xs font-medium text-yellow-800 mb-1">Recommendation</p>
                    <p className="text-yellow-900 leading-relaxed line-clamp-3">{r.recommendation_snapshot}</p>
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  <Button size="sm" onClick={() => { setSelected(r); setModal("approve"); }}>
                    <CheckCircle className="h-4 w-4 mr-1" />Approve
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => { setSelected(r); setModal("reject"); }}>
                    <XCircle className="h-4 w-4 mr-1" />Reject
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => {
                    setSelected(r);
                    setModText(r.recommendation_snapshot ?? "");
                    setModal("modify");
                  }}>
                    <Edit3 className="h-4 w-4 mr-1" />Modify
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* All reviews table */}
      <Card>
        <CardHeader>
          <CardTitle>All Reviews ({reviews.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="text-center py-10 text-muted-foreground">Loading…</div>
          ) : reviews.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground">No reviews yet. Create one from an anomaly.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  {["Anomaly Record", "Dataset", "Status", "Reviewed By", "Reviewed At", "Comments"].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {reviews.map(r => (
                  <tr key={r.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs truncate max-w-[180px]">{r.anomaly_record_id}</td>
                    <td className="px-4 py-3 capitalize">{r.dataset}</td>
                    <td className="px-4 py-3"><Badge variant={statusVariant(r.status)}>{r.status.replace("_", " ")}</Badge></td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{r.reviewed_by ?? "—"}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{r.reviewed_at ? formatDate(r.reviewed_at) : "—"}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground max-w-[200px] truncate">{r.review_comments ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* ── Approve Modal ── */}
      <Modal isOpen={modal === "approve"} onClose={closeModal} title="Approve Recommendation">
        <div className="space-y-4">
          <p className="text-sm">Approve the recommendation for <span className="font-mono font-medium">{selected?.anomaly_record_id}</span>. This will allow an action to be created.</p>
          {selected?.recommendation_snapshot && (
            <div className="p-3 bg-muted rounded-lg text-sm">{selected.recommendation_snapshot}</div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Optional Comment</label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={3}
                      placeholder="Add approval notes…" value={comment}
                      onChange={e => setComment(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleApprove} disabled={saving}>{saving ? "Saving…" : "Confirm Approval"}</Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* ── Reject Modal ── */}
      <Modal isOpen={modal === "reject"} onClose={closeModal} title="Reject Recommendation">
        <div className="space-y-4">
          <p className="text-sm">Reject the recommendation for <span className="font-mono font-medium">{selected?.anomaly_record_id}</span>.</p>
          <div>
            <label className="block text-sm font-medium mb-1">Rejection Reason <span className="text-red-600">*</span></label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={4}
                      placeholder="Explain why this recommendation is not appropriate…"
                      value={comment} onChange={e => setComment(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button variant="danger" onClick={handleReject} disabled={saving || !comment.trim()}>
              {saving ? "Saving…" : "Confirm Rejection"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* ── Modify Modal ── */}
      <Modal isOpen={modal === "modify"} onClose={closeModal} title="Modify Recommendation">
        <div className="space-y-4">
          <p className="text-sm">Edit the recommendation text, then save. The review will be marked <strong>modified</strong> and available for final approval.</p>
          <div>
            <label className="block text-sm font-medium mb-1">Modified Recommendation <span className="text-red-600">*</span></label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={5}
                      value={modText} onChange={e => setModText(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Comment</label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={2}
                      placeholder="Explain what you changed…" value={comment}
                      onChange={e => setComment(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleModify} disabled={saving || !modText.trim()}>
              {saving ? "Saving…" : "Save Modification"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* ── Create Review Modal ── */}
      <Modal isOpen={modal === "create"} onClose={() => setModal(null)} title="Create New Review">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Create a human review entry for a specific anomaly record.</p>
          <div>
            <label className="block text-sm font-medium mb-1">Anomaly Record ID <span className="text-red-600">*</span></label>
            <input className="w-full px-3 py-2 border rounded-md text-sm font-mono"
                   placeholder="e.g. CLAIMS-10091OR0770001"
                   value={createRecordId} onChange={e => setCreateRecordId(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Dataset</label>
            <select className="w-full px-3 py-2 border rounded-md text-sm"
                    value={createDataset} onChange={e => setCreateDataset(e.target.value)}>
              <option value="claims">Claims</option>
              <option value="authorization">Authorization</option>
              <option value="pharmacy">Pharmacy</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Recommendation (optional)</label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={4}
                      placeholder="Paste the AI recommendation here…"
                      value={createSnapshot} onChange={e => setCreateSnapshot(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={saving || !createRecordId.trim()}>
              {saving ? "Creating…" : "Create Review"}
            </Button>
            <Button variant="outline" onClick={() => setModal(null)}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
