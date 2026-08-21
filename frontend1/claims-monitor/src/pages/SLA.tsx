import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { DataTable, type Column } from "../components/ui/DataTable";
import { getSLAItems } from "../services/api";
import { calculateSLAStatus, formatDate } from "../lib/utils";
import { Clock, AlertCircle, CheckCircle } from "lucide-react";
import type { SLAItem } from "../types";

export function SLA() {
  const [items, setItems] = useState<SLAItem[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<string>("All");

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    const data = await getSLAItems();
    setItems(data);
  };

  const filteredItems =
    priorityFilter === "All"
      ? items
      : items.filter((item) => item.priority === priorityFilter);

  const columns: Column<SLAItem>[] = [
    {
      key: "title",
      label: "Issue",
      sortable: true,
      render: (row) => (
        <div>
          <div className="font-medium">{row.title}</div>
          <div className="text-xs text-muted-foreground">{row.source}</div>
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
      label: "SLA",
      sortable: true,
      render: (row) => `${row.slaHours}h`,
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
                <AlertCircle className="h-4 w-4 text-red-600" />
                <span className="text-red-600 font-medium">Breached</span>
              </>
            ) : slaStatus.status === "at_risk" ? (
              <>
                <Clock className="h-4 w-4 text-orange-600" />
                <span className="text-orange-600 font-medium">At Risk</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-600">On Track</span>
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
          <span className={slaStatus.isBreached ? "text-red-600 font-medium" : ""}>
            {slaStatus.isBreached
              ? "Overdue"
              : `${slaStatus.hoursLeft.toFixed(1)}h left`}
          </span>
        );
      },
    },
    {
      key: "estimatedResolutionTime",
      label: "Est. Resolution",
      sortable: true,
      render: (row) => `${row.estimatedResolutionTime}h`,
    },
    {
      key: "assignedTo",
      label: "Assigned To",
      sortable: true,
      render: (row) => row.assignedTo || "Unassigned",
    },
    {
      key: "detectedTime",
      label: "Detected",
      sortable: true,
      render: (row) => <span className="text-xs">{formatDate(row.detectedTime)}</span>,
    },
  ];

  const breached = items.filter(
    (item) => calculateSLAStatus(item.detectedTime, item.slaHours).isBreached
  );
  const atRisk = items.filter(
    (item) =>
      calculateSLAStatus(item.detectedTime, item.slaHours).status === "at_risk"
  );
  const onTrack = items.filter(
    (item) =>
      calculateSLAStatus(item.detectedTime, item.slaHours).status === "on_track"
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">SLA & Priority Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Monitor SLA compliance and prioritize resolution efforts
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Items
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{items.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              SLA Breached
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <div className="text-2xl font-bold text-red-600">{breached.length}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              At Risk
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <div className="text-2xl font-bold text-orange-600">{atRisk.length}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              On Track
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div className="text-2xl font-bold text-green-600">{onTrack.length}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SLA Risk Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-red-600 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Breached ({breached.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {breached.length === 0 ? (
              <p className="text-sm text-muted-foreground">No breached items</p>
            ) : (
              <div className="space-y-2">
                {breached.map((item) => (
                  <div key={item.id} className="p-3 border border-red-200 rounded-lg bg-red-50">
                    <div className="font-medium text-sm">{item.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Priority: {item.priority} | Assigned: {item.assignedTo || "Unassigned"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-orange-600 flex items-center gap-2">
              <Clock className="h-5 w-5" />
              At Risk ({atRisk.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {atRisk.length === 0 ? (
              <p className="text-sm text-muted-foreground">No at-risk items</p>
            ) : (
              <div className="space-y-2">
                {atRisk.map((item) => (
                  <div key={item.id} className="p-3 border border-orange-200 rounded-lg bg-orange-50">
                    <div className="font-medium text-sm">{item.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {calculateSLAStatus(item.detectedTime, item.slaHours).hoursLeft.toFixed(1)}h left
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-green-600 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              On Track ({onTrack.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {onTrack.length === 0 ? (
              <p className="text-sm text-muted-foreground">No items on track</p>
            ) : (
              <div className="space-y-2">
                {onTrack.slice(0, 3).map((item) => (
                  <div key={item.id} className="p-3 border border-green-200 rounded-lg bg-green-50">
                    <div className="font-medium text-sm">{item.title}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {calculateSLAStatus(item.detectedTime, item.slaHours).hoursLeft.toFixed(1)}h left
                    </div>
                  </div>
                ))}
                {onTrack.length > 3 && (
                  <div className="text-xs text-muted-foreground text-center">
                    +{onTrack.length - 3} more
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle>All SLA Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex items-center gap-2">
            <span className="text-sm font-medium">Priority:</span>
            {["All", "High", "Medium", "Low"].map((priority) => (
              <button
                key={priority}
                onClick={() => setPriorityFilter(priority)}
                className={`px-3 py-1 rounded-md text-sm transition-colors ${
                  priorityFilter === priority
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary hover:bg-secondary/80"
                }`}
              >
                {priority}
              </button>
            ))}
          </div>

          <DataTable data={filteredItems} columns={columns} />
        </CardContent>
      </Card>
    </div>
  );
}
