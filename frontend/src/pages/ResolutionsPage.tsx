import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import {
  getActions, getReviews, createAction, assignAction, updateActionStatus,
  getWorkers,
  type ActionRecord, type ReviewRecord,
} from "../services/integratedApi";
import { formatDate } from "../lib/utils";
import {
  PlayCircle, CheckCircle, XCircle, Clock,
  UserCheck, RefreshCw, Plus, AlertTriangle,
} from "lucide-react";

type ModalType = "create" | "assign" | "status" | null;

const STATUS_COLORS: Record<string, string> = {
  created:     "bg-gray-100 text-gray-700 border-gray-200",
  assigned:    "bg-blue-100 text-blue-700 border-blue-200",
  in_progress: "bg-yellow-100 text-yellow-700 border-yellow-200",
  completed:   "bg-green-100 text-green-700 border-green-200",
  failed:      "bg-red-100 text-red-700 border-red-200",
};

const ACTION_TYPES = ["Fix Data", "Reprocess", "Escalate", "Contact Team"];

export function ResolutionsPage() {
  const [actions,  setActions]  = useState<ActionRecord[]>([]);
  const [reviews,  setReviews]  = useState<ReviewRecord[]>([]);
  const [workers,  setWorkers]  = useState<{ id: string; name: string; email: string; is_active: boolean }[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [saving,   setSaving]   = useState(false);
  const [modal,    setModal]    = useState<ModalType>(null);
  const [selected, setSelected] = useState<ActionRecord | null>(null);

  // create form
  const [selReviewId,   setSelReviewId]   = useState("");
  const [selActionType, setSelActionType] = useState("Fix Data");
  const [description,   setDescription]  = useState("");

  // assign form
  const [selWorkerId, setSelWorkerId] = useState("");

  // status form
  const [newStatus,        setNewStatus]        = useState("");
  const [statusNotes,      setStatusNotes]      = useState("");
  const [resolutionNotes,  setResolutionNotes]  = useState("");

  const [filterStatus, setFilterStatus] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [a, r, w] = await Promise.all([
        getActions({ status: filterStatus || undefined }),
        getReviews({ status: "approved" }),
        getWorkers(),
      ]);
      setActions(a);
      setReviews(r);
      setWorkers(w.filter(w => w.is_active));
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to load");
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filterStatus]);

  const closeModal = () => {
    setModal(null); setSelected(null);
    setSelReviewId(""); setSelActionType("Fix Data"); setDescription("");
    setSelWorkerId(""); setNewStatus(""); setStatusNotes(""); setResolutionNotes("");
  };

  const handleCreate = async () => {
    if (!selReviewId) return;
    setSaving(true);
    try {
      await createAction({ review_id: selReviewId, action_type: selActionType, description: description || undefined });
      await load(); closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const handleAssign = async () => {
    if (!selected || !selWorkerId) return;
    setSaving(true);
    try {
      await assignAction(selected.id, selWorkerId);
      await load(); closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const handleStatusUpdate = async () => {
    if (!selected || !newStatus) return;
    setSaving(true);
    try {
      await updateActionStatus(selected.id, {
        status: newStatus,
        notes: statusNotes || undefined,
        resolution_notes: resolutionNotes || undefined,
      });
      await load(); closeModal();
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed");
    } finally { setSaving(false); }
  };

  const counts = {
    created:     actions.filter(a => a.status === "created").length,
    assigned:    actions.filter(a => a.status === "assigned").length,
    in_progress: actions.filter(a => a.status === "in_progress").length,
    completed:   actions.filter(a => a.status === "completed").length,
    failed:      actions.filter(a => a.status === "failed").length,
  };

  const allowedNext: Record<string, string[]> = {
    created:     ["assigned", "in_progress"],
    assigned:    ["in_progress"],
    in_progress: ["completed", "failed"],
    completed:   [],
    failed:      [],
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Execute Actions &amp; Resolution Tracking</h1>
          <p className="text-muted-foreground mt-1">
            Create and track actions from approved recommendations
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button size="sm" onClick={() => setModal("create")}>
            <Plus className="h-4 w-4 mr-2" />New Action
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />{error}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: "Created",     value: counts.created,     icon: PlayCircle, color: "text-gray-600"   },
          { label: "Assigned",    value: counts.assigned,    icon: UserCheck,  color: "text-blue-600"   },
          { label: "In Progress", value: counts.in_progress, icon: Clock,      color: "text-yellow-600" },
          { label: "Completed",   value: counts.completed,   icon: CheckCircle,color: "text-green-600"  },
          { label: "Failed",      value: counts.failed,      icon: XCircle,    color: "text-red-600"    },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                <Icon className={`h-4 w-4 ${color}`} />{label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Kanban lanes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { key: "created",     label: "Created",     color: "border-gray-200",  bg: "bg-gray-50"    },
          { key: "in_progress", label: "In Progress", color: "border-yellow-200",bg: "bg-yellow-50"  },
          { key: "completed",   label: "Completed",   color: "border-green-200", bg: "bg-green-50"   },
        ].map(lane => (
          <Card key={lane.key}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">{lane.label} ({actions.filter(a => a.status === lane.key).length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-64 overflow-y-auto">
              {actions.filter(a => a.status === lane.key).length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-4">No items</p>
              ) : actions.filter(a => a.status === lane.key).map(a => (
                <div key={a.id} className={`p-3 border ${lane.color} rounded-lg ${lane.bg}`}>
                  <p className="text-xs font-mono font-medium truncate">{a.anomaly_record_id}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="info">{a.action_type}</Badge>
                    <span className="text-xs text-muted-foreground capitalize">{a.dataset}</span>
                  </div>
                  {a.assigned_to && (
                    <p className="text-xs text-muted-foreground mt-1">Assigned: {a.assigned_to.slice(0, 8)}…</p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Status filter + full table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <CardTitle>All Actions ({actions.length})</CardTitle>
            <div className="flex flex-wrap gap-2">
              {["", "created", "assigned", "in_progress", "completed", "failed"].map(v => (
                <button key={v} onClick={() => setFilterStatus(v)}
                        className={`px-3 py-1 rounded-md text-xs transition-colors ${
                          filterStatus === v
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary hover:bg-secondary/80"
                        }`}>
                  {v === "" ? "All" : v.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="text-center py-10 text-muted-foreground">Loading…</div>
          ) : actions.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground">
              No actions yet. Create one from an approved review.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    {["Anomaly Record", "Dataset", "Type", "Status", "Assigned To", "Created", "Actions"].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {actions.map(a => (
                    <tr key={a.id} className="border-b hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs max-w-[160px] truncate">{a.anomaly_record_id}</td>
                      <td className="px-4 py-3 capitalize text-xs">{a.dataset}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 rounded-full text-xs border bg-blue-50 text-blue-700 border-blue-200">
                          {a.action_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[a.status] ?? ""}`}>
                          {a.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">
                        {a.assigned_to
                          ? workers.find(w => w.id === a.assigned_to)?.name ?? a.assigned_to.slice(0, 8) + "…"
                          : "Unassigned"}
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(a.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {!a.assigned_to && a.status === "created" && (
                            <button onClick={() => { setSelected(a); setModal("assign"); }}
                                    className="text-xs px-2 py-1 rounded border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors">
                              Assign
                            </button>
                          )}
                          {allowedNext[a.status]?.length > 0 && (
                            <button onClick={() => {
                              setSelected(a);
                              setNewStatus(allowedNext[a.status][0]);
                              setModal("status");
                            }}
                            className="text-xs px-2 py-1 rounded border border-gray-200 bg-gray-50 hover:bg-gray-100 transition-colors">
                              Update
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Create Action Modal ── */}
      <Modal isOpen={modal === "create"} onClose={closeModal} title="Create New Action">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Actions can only be created from <strong>approved</strong> reviews ({reviews.length} available).
          </p>
          <div>
            <label className="block text-sm font-medium mb-1">Approved Review <span className="text-red-600">*</span></label>
            <select className="w-full px-3 py-2 border rounded-md text-sm"
                    value={selReviewId} onChange={e => setSelReviewId(e.target.value)}>
              <option value="">Select a review…</option>
              {reviews.map(r => (
                <option key={r.id} value={r.id}>
                  {r.anomaly_record_id} ({r.dataset})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Action Type</label>
            <select className="w-full px-3 py-2 border rounded-md text-sm"
                    value={selActionType} onChange={e => setSelActionType(e.target.value)}>
              {ACTION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={3}
                      placeholder="Describe what needs to be done…"
                      value={description} onChange={e => setDescription(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <Button onClick={handleCreate} disabled={saving || !selReviewId}>
              {saving ? "Creating…" : "Create Action"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* ── Assign Modal ── */}
      <Modal isOpen={modal === "assign"} onClose={closeModal} title="Assign Action to Worker">
        <div className="space-y-4">
          <p className="text-sm">Assigning action for <span className="font-mono">{selected?.anomaly_record_id}</span></p>
          <div>
            <label className="block text-sm font-medium mb-1">Select Worker <span className="text-red-600">*</span></label>
            <select className="w-full px-3 py-2 border rounded-md text-sm"
                    value={selWorkerId} onChange={e => setSelWorkerId(e.target.value)}>
              <option value="">Choose a worker…</option>
              {workers.map(w => (
                <option key={w.id} value={w.id}>{w.name} ({w.email})</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleAssign} disabled={saving || !selWorkerId}>
              {saving ? "Assigning…" : "Assign Worker"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>

      {/* ── Status Update Modal ── */}
      <Modal isOpen={modal === "status"} onClose={closeModal} title="Update Action Status">
        <div className="space-y-4">
          <p className="text-sm">Updating <span className="font-mono">{selected?.anomaly_record_id}</span> — current status: <strong>{selected?.status}</strong></p>
          <div>
            <label className="block text-sm font-medium mb-1">New Status <span className="text-red-600">*</span></label>
            <select className="w-full px-3 py-2 border rounded-md text-sm"
                    value={newStatus} onChange={e => setNewStatus(e.target.value)}>
              <option value="">Select status…</option>
              {(allowedNext[selected?.status ?? ""] ?? []).map(s => (
                <option key={s} value={s}>{s.replace("_", " ")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Progress Notes</label>
            <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={3}
                      placeholder="What was done…"
                      value={statusNotes} onChange={e => setStatusNotes(e.target.value)} />
          </div>
          {(newStatus === "completed" || newStatus === "failed") && (
            <div>
              <label className="block text-sm font-medium mb-1">Resolution Notes</label>
              <textarea className="w-full px-3 py-2 border rounded-md text-sm" rows={3}
                        placeholder="How was this resolved / why did it fail…"
                        value={resolutionNotes} onChange={e => setResolutionNotes(e.target.value)} />
            </div>
          )}
          <div className="flex gap-2">
            <Button onClick={handleStatusUpdate} disabled={saving || !newStatus}>
              {saving ? "Saving…" : "Update Status"}
            </Button>
            <Button variant="outline" onClick={closeModal}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
