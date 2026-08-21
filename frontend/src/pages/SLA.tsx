import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { Badge } from "../components/ui/Badge";
import { calculateSLAStatus, formatDate } from "../lib/utils";
import { Clock, AlertCircle, CheckCircle, RefreshCw, ArrowUpRight, Search, Eye, Sparkles } from "lucide-react";
import type { SLAItem } from "../types";

const INITIAL_SLA_ITEMS: SLAItem[] = [
  {
    id: "sla-001",
    title: "Prior Auth SLA Window - Inpatient Medication",
    source: "Authorization System",
    priority: "High",
    slaHours: 24,
    detectedTime: new Date(Date.now() - 28 * 3600 * 1000).toISOString(), // Breached
    estimatedResolutionTime: 2,
    assignedTo: "Agalya",
    status: "breached",
  },
  {
    id: "sla-002",
    title: "Duplicate Claims Spike - Urgent Care Feed",
    source: "Claims Data Feed",
    priority: "High",
    slaHours: 24,
    detectedTime: new Date(Date.now() - 26 * 3600 * 1000).toISOString(), // Breached
    estimatedResolutionTime: 3,
    assignedTo: "Sarah Johnson",
    status: "breached",
  },
  {
    id: "sla-003",
    title: "Approval Workflow Timeout - Surgical Referral",
    source: "Authorization System",
    priority: "High",
    slaHours: 24,
    detectedTime: new Date(Date.now() - 23 * 3600 * 1000).toISOString(), // At Risk (~1h left)
    estimatedResolutionTime: 1.5,
    assignedTo: "Mike Chen",
    status: "at_risk",
  },
  {
    id: "sla-004",
    title: "Missing NPI Data - Prescriber Database",
    source: "Prescriber Database",
    priority: "Medium",
    slaHours: 24,
    detectedTime: new Date(Date.now() - 20 * 3600 * 1000).toISOString(), // At Risk (~4h left)
    estimatedResolutionTime: 4,
    assignedTo: "middle-man",
    status: "at_risk",
  },
  {
    id: "sla-005",
    title: "NDC Code Mismatch - Speciality Pharmacy",
    source: "Pharmacy Network",
    priority: "Medium",
    slaHours: 24,
    detectedTime: new Date(Date.now() - 19 * 3600 * 1000).toISOString(), // At Risk (~5h left)
    estimatedResolutionTime: 2,
    assignedTo: "David Kim",
    status: "at_risk",
  },
  {
    id: "sla-006",
    title: "Outpatient Pre-Auth Verification",
    source: "Authorization System",
    priority: "Low",
    slaHours: 48,
    detectedTime: new Date(Date.now() - 10 * 3600 * 1000).toISOString(), // On Track
    estimatedResolutionTime: 5,
    assignedTo: "Worker User",
    status: "on_track",
  },
  {
    id: "sla-007",
    title: "EHR Diagnosis Code Validation Queue",
    source: "Claims Data Feed",
    priority: "Medium",
    slaHours: 48,
    detectedTime: new Date(Date.now() - 12 * 3600 * 1000).toISOString(), // On Track
    estimatedResolutionTime: 4,
    assignedTo: "Agalya",
    status: "on_track",
  },
  {
    id: "sla-008",
    title: "High-Value Specialty Claim Audit",
    source: "Claims Data Feed",
    priority: "High",
    slaHours: 72,
    detectedTime: new Date(Date.now() - 15 * 3600 * 1000).toISOString(), // On Track
    estimatedResolutionTime: 6,
    assignedTo: "Sarah Johnson",
    status: "on_track",
  },
];

export function SLA() {
  const [items, setItems] = useState<SLAItem[]>(INITIAL_SLA_ITEMS);
  const [priorityFilter, setPriorityFilter] = useState<string>("All");
  const [sourceFilter, setSourceFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedItem, setSelectedItem] = useState<SLAItem | null>(null);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const handleExtendSLA = (id: string) => {
    setItems((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          // Add 24h to detected time so deadline extends forward
          const extendedTime = new Date(new Date(item.detectedTime).getTime() + 24 * 3600 * 1000).toISOString();
          return { ...item, detectedTime: extendedTime };
        }
        return item;
      })
    );
    if (selectedItem?.id === id) setSelectedItem(null);

    setActionSuccessMsg(`SLA deadline extended by +24 hours for ${id}.`);
    setTimeout(() => setActionSuccessMsg(null), 5000);
  };

  const handleReassign = (id: string, newAssignee: string) => {
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, assignedTo: newAssignee } : item))
    );
    if (selectedItem?.id === id) {
      setSelectedItem((prev) => (prev ? { ...prev, assignedTo: newAssignee } : null));
    }

    setActionSuccessMsg(`Item ${id} reassigned to ${newAssignee}.`);
    setTimeout(() => setActionSuccessMsg(null), 5000);
  };

  const handleResolveSLA = (id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
    setSelectedItem(null);

    setActionSuccessMsg(`SLA Item ${id} marked as resolved and removed from tracking queue.`);
    setTimeout(() => setActionSuccessMsg(null), 5000);
  };

  const filteredItems = items.filter((item) => {
    if (priorityFilter !== "All" && item.priority !== priorityFilter) return false;
    if (sourceFilter !== "All" && item.source !== sourceFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchSource = item.source.toLowerCase().includes(q);
      const matchAssignee = item.assignedTo ? item.assignedTo.toLowerCase().includes(q) : false;
      if (!matchTitle && !matchSource && !matchAssignee) return false;
    }
    return true;
  });

  const columns: Column<SLAItem>[] = [
    {
      key: "title",
      label: "Issue / Pipeline Target",
      sortable: true,
      render: (row) => (
        <div
          className="cursor-pointer group hover:text-blue-600 transition-colors"
          onClick={() => setSelectedItem(row)}
        >
          <div className="font-semibold text-slate-900 group-hover:text-blue-600 flex items-center gap-1.5">
            <span>{row.title}</span>
            <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-blue-600" />
          </div>
          <div className="text-xs text-slate-500 font-mono mt-0.5">{row.source}</div>
        </div>
      ),
    },
    {
      key: "priority",
      label: "Priority",
      sortable: true,
      render: (row) => <StatusBadge status={row.priority} type="priority" />,
    },
    {
      key: "slaHours",
      label: "SLA Window",
      sortable: true,
      render: (row) => <span className="font-mono text-slate-700 text-xs font-semibold">{row.slaHours}h</span>,
    },
    {
      key: "status",
      label: "SLA Status",
      sortable: true,
      render: (row) => {
        const slaStatus = calculateSLAStatus(row.detectedTime, row.slaHours);
        return (
          <div className="flex items-center gap-2">
            {slaStatus.status === "breached" ? (
              <>
                <AlertCircle className="h-4 w-4 text-rose-600" />
                <span className="text-rose-600 font-bold text-xs">Breached</span>
              </>
            ) : slaStatus.status === "at_risk" ? (
              <>
                <Clock className="h-4 w-4 text-amber-500" />
                <span className="text-amber-600 font-bold text-xs">At Risk</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <span className="text-emerald-700 font-semibold text-xs">On Track</span>
              </>
            )}
          </div>
        );
      },
    },
    {
      key: "detectedTime",
      label: "Time Remaining",
      sortable: true,
      render: (row) => {
        const slaStatus = calculateSLAStatus(row.detectedTime, row.slaHours);
        return (
          <span className={`font-mono text-xs ${slaStatus.isBreached ? "text-rose-600 font-bold" : slaStatus.status === "at_risk" ? "text-amber-600 font-semibold" : "text-slate-700"}`}>
            {slaStatus.isBreached
              ? "Overdue"
              : `${slaStatus.hoursLeft.toFixed(1)}h left`}
          </span>
        );
      },
    },
    {
      key: "assignedTo",
      label: "Assigned Steward",
      sortable: true,
      render: (row) => (
        <span className="text-xs font-semibold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-md">
          {row.assignedTo || "Unassigned"}
        </span>
      ),
    },
    {
      key: "id",
      label: "Actions",
      render: (row) => (
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleExtendSLA(row.id)}
            className="p-1 rounded-lg text-blue-600 hover:bg-blue-50 transition-all text-xs font-semibold px-2 py-1 border border-blue-200"
            title="Extend SLA +24h"
          >
            +24h
          </button>
          <button
            onClick={() => setSelectedItem(row)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  const breached = items.filter(
    (item) => calculateSLAStatus(item.detectedTime, item.slaHours).isBreached
  );
  const atRisk = items.filter(
    (item) => calculateSLAStatus(item.detectedTime, item.slaHours).status === "at_risk"
  );
  const onTrack = items.filter(
    (item) => calculateSLAStatus(item.detectedTime, item.slaHours).status === "on_track"
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">SLA & Priority Dashboard</h1>
            <Badge variant="info">Live SLA Telemetry</Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Monitor resolution deadlines, SLA compliance tiers, and worker assignments across data feeds
          </p>
        </div>

        <button
          onClick={() => {
            setItems(INITIAL_SLA_ITEMS);
            setActionSuccessMsg("SLA state reset to default baselines.");
            setTimeout(() => setActionSuccessMsg(null), 4000);
          }}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 shadow-xs transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-600" />
          <span>Refresh SLA Queue</span>
        </button>
      </div>

      {actionSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-xs animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-semibold">{actionSuccessMsg}</span>
          </div>
          <span className="text-[11px] text-emerald-600 font-mono">Updated</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 font-mono">{items.length}</div>
            <p className="text-xs text-slate-400 mt-1">Active resolution queue</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              SLA Breached
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-rose-600" />
              <div className="text-2xl font-bold text-rose-600 font-mono">{breached.length}</div>
            </div>
            <p className="text-xs text-rose-600 mt-1 font-medium">Escalation required</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              At Risk
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-500" />
              <div className="text-2xl font-bold text-amber-600 font-mono">{atRisk.length}</div>
            </div>
            <p className="text-xs text-amber-600 mt-1 font-medium">&lt; 6 hours remaining</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              On Track
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <div className="text-2xl font-bold text-emerald-600 font-mono">{onTrack.length}</div>
            </div>
            <p className="text-xs text-emerald-600 mt-1 font-medium">Meeting SLA targets</p>
          </CardContent>
        </Card>
      </div>

      {/* SLA Kanban Board: Breached | At Risk | On Track */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Breached Column */}
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-rose-600 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-rose-600" />
                <span>Breached ({breached.length})</span>
              </CardTitle>
              <span className="text-xs text-rose-600 bg-rose-50 px-2 py-0.5 rounded font-mono font-semibold">Overdue</span>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {breached.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                <CheckCircle className="w-6 h-6 text-emerald-500 mx-auto mb-1 opacity-80" />
                No breached SLA items. All issues are on track!
              </div>
            ) : (
              breached.map((item) => (
                <div key={item.id} className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-semibold text-xs text-slate-900 leading-snug">{item.title}</span>
                    <Badge variant="error">{item.priority}</Badge>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center justify-between">
                    <span>Source: <strong className="text-slate-700">{item.source}</strong></span>
                    <span>Steward: <strong className="text-slate-800">{item.assignedTo || "Unassigned"}</strong></span>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-rose-200/60">
                    <span className="text-[11px] font-mono font-bold text-rose-700">Deadline Passed</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleExtendSLA(item.id)}
                        className="px-2 py-0.5 rounded text-[11px] font-semibold text-blue-700 bg-white border border-blue-200 hover:bg-blue-50 transition-all"
                      >
                        +24h SLA
                      </button>
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="px-2 py-0.5 rounded text-[11px] font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-all"
                      >
                        Inspect
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* At Risk Column */}
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-amber-600 flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-500" />
                <span>At Risk ({atRisk.length})</span>
              </CardTitle>
              <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded font-mono font-semibold">&lt;6h Left</span>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {atRisk.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No items currently at risk of SLA breach.
              </div>
            ) : (
              atRisk.map((item) => {
                const hoursLeft = calculateSLAStatus(item.detectedTime, item.slaHours).hoursLeft.toFixed(1);
                return (
                  <div key={item.id} className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-xs text-slate-900 leading-snug">{item.title}</span>
                      <Badge variant="warning">{item.priority}</Badge>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center justify-between">
                      <span>Source: <strong className="text-slate-700">{item.source}</strong></span>
                      <span>Steward: <strong className="text-slate-800">{item.assignedTo || "Unassigned"}</strong></span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-amber-200/60">
                      <span className="text-[11px] font-mono font-bold text-amber-700">{hoursLeft}h remaining</span>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => handleExtendSLA(item.id)}
                          className="px-2 py-0.5 rounded text-[11px] font-semibold text-blue-700 bg-white border border-blue-200 hover:bg-blue-50 transition-all"
                        >
                          +24h
                        </button>
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="px-2 py-0.5 rounded text-[11px] font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-all"
                        >
                          Inspect
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        {/* On Track Column */}
        <Card className="bg-white border-slate-200 shadow-xs">
          <CardHeader className="pb-3 border-b border-slate-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold text-emerald-600 flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <span>On Track ({onTrack.length})</span>
              </CardTitle>
              <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-mono font-semibold">Meeting Target</span>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {onTrack.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No active items on track.
              </div>
            ) : (
              onTrack.map((item) => {
                const hoursLeft = calculateSLAStatus(item.detectedTime, item.slaHours).hoursLeft.toFixed(1);
                return (
                  <div key={item.id} className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-xs text-slate-900 leading-snug">{item.title}</span>
                      <Badge variant="success">{item.priority}</Badge>
                    </div>
                    <div className="text-[11px] text-slate-500 flex items-center justify-between">
                      <span>Source: <strong className="text-slate-700">{item.source}</strong></span>
                      <span>Steward: <strong className="text-slate-800">{item.assignedTo || "Unassigned"}</strong></span>
                    </div>
                    <div className="flex items-center justify-between pt-1 border-t border-emerald-200/60">
                      <span className="text-[11px] font-mono font-bold text-emerald-700">{hoursLeft}h remaining</span>
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="px-2 py-0.5 rounded text-[11px] font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 transition-all"
                      >
                        Inspect
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      {/* Items Table */}
      <Card className="bg-white border-slate-200 shadow-xs">
        <CardHeader className="pb-4 border-b border-slate-100">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-base font-bold text-slate-900">All Active SLA Tracking Queue</CardTitle>
              <CardDescription className="text-xs text-slate-500 mt-0.5">
                Filter by priority level, data source, or search issue title
              </CardDescription>
            </div>

            {/* Search & Source Filter */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search SLA issue..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 text-slate-700 w-44"
                />
              </div>

              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="py-1.5 px-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 text-slate-700 font-medium"
              >
                <option value="All">All Data Feeds</option>
                <option value="Authorization System">Authorization System</option>
                <option value="Claims Data Feed">Claims Data Feed</option>
                <option value="Pharmacy Network">Pharmacy Network</option>
                <option value="Prescriber Database">Prescriber Database</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <div className="flex flex-wrap gap-1.5 pb-2 border-b border-slate-100">
            {["All", "High", "Medium", "Low"].map((priority) => (
              <button
                key={priority}
                onClick={() => setPriorityFilter(priority)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  priorityFilter === priority
                    ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs"
                    : "bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                {priority === "All" ? "All Priorities" : `${priority} Priority`}
              </button>
            ))}
          </div>

          <DataTable data={filteredItems} columns={columns} />
        </CardContent>
      </Card>

      {/* SLA Inspection & Override Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-base">SLA Item Inspection</h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 text-[11px] block">Issue Title</span>
                <span className="font-bold text-slate-900 text-sm">{selectedItem.title}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-400 text-[11px] block">Source Pipeline</span>
                  <span className="font-semibold text-slate-800">{selectedItem.source}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[11px] block">Priority Tier</span>
                  <span className="font-bold text-blue-700">{selectedItem.priority}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[11px] block">SLA Target Window</span>
                  <span className="font-mono font-bold text-slate-800">{selectedItem.slaHours} Hours</span>
                </div>
                <div>
                  <span className="text-slate-400 text-[11px] block">Detected At</span>
                  <span className="font-mono text-slate-700">{formatDate(selectedItem.detectedTime)}</span>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-800 block mb-1">Assigned Steward</label>
                <select
                  value={selectedItem.assignedTo || "Unassigned"}
                  onChange={(e) => handleReassign(selectedItem.id, e.target.value)}
                  className="w-full py-2 px-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 focus:outline-none focus:border-blue-500"
                >
                  <option value="middle-man">middle-man (Operator)</option>
                  <option value="Agalya">Agalya (Lead Steward)</option>
                  <option value="Sarah Johnson">Sarah Johnson (Claims Manager)</option>
                  <option value="Mike Chen">Mike Chen (Auth Specialist)</option>
                  <option value="David Kim">David Kim (Pharmacy Steward)</option>
                  <option value="Worker User">Worker User (Operator)</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-100">
              <button
                onClick={() => handleExtendSLA(selectedItem.id)}
                className="px-3.5 py-2 rounded-lg text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 hover:bg-blue-100 transition-all"
              >
                +24h SLA Extension
              </button>
              <button
                onClick={() => handleResolveSLA(selectedItem.id)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 transition-all"
                style={{ background: "#059669" }}
              >
                Mark Issue Resolved
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
