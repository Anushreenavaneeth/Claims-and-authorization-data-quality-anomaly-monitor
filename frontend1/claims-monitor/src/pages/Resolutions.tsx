import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/shared/StatusBadge";
import { Badge } from "../components/ui/Badge";
import { getResolutions } from "../services/api";
import { formatDate, calculateSLAStatus } from "../lib/utils";
import { PlayCircle, Clock, CheckCircle, XCircle } from "lucide-react";
import type { Resolution } from "../types";

export function Resolutions() {
  const [resolutions, setResolutions] = useState<Resolution[]>([]);

  useEffect(() => {
    loadResolutions();
  }, []);

  const loadResolutions = async () => {
    const data = await getResolutions();
    setResolutions(data);
  };

  const getActionTypeColor = (actionType: string) => {
    switch (actionType) {
      case "Fix Data":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "Reprocess Claims":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "Escalate/Contact Team":
        return "bg-orange-50 text-orange-700 border-orange-200";
      default:
        return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const groupedByActionType = {
    "Fix Data": resolutions.filter((r) => r.actionType === "Fix Data"),
    "Reprocess Claims": resolutions.filter((r) => r.actionType === "Reprocess Claims"),
    "Escalate/Contact Team": resolutions.filter((r) => r.actionType === "Escalate/Contact Team"),
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Execute Actions & Resolution Tracking</h1>
        <p className="text-muted-foreground mt-1">
          Track and manage resolution actions across all workflows
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Resolutions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resolutions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              In Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {resolutions.filter((r) => r.status === "in_progress").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {resolutions.filter((r) => r.status === "completed").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {resolutions.filter((r) => r.status === "pending").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Kanban-style Board */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {Object.entries(groupedByActionType).map(([actionType, items]) => (
          <Card key={actionType}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PlayCircle className="h-5 w-5" />
                {actionType}
                <span className="ml-auto text-sm font-normal text-muted-foreground">
                  ({items.length})
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {items.length === 0 ? (
                <p className="text-center py-8 text-muted-foreground text-sm">
                  No items in this category
                </p>
              ) : (
                <div className="space-y-3">
                  {items.map((resolution) => {
                    const slaStatus = calculateSLAStatus(
                      resolution.startTime || resolution.slaDeadline,
                      24
                    );
                    
                    return (
                      <div
                        key={resolution.id}
                        className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="font-medium text-sm">
                              Anomaly: {resolution.anomalyId}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Assigned to: {resolution.assignedTo}
                            </div>
                          </div>
                          <StatusBadge status={resolution.status} />
                        </div>

                        {/* Progress Info */}
                        <div className="space-y-2 text-sm">
                          {resolution.startTime && (
                            <div className="flex items-center gap-2 text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span className="text-xs">
                                Started: {formatDate(resolution.startTime)}
                              </span>
                            </div>
                          )}

                          {resolution.completedTime && (
                            <div className="flex items-center gap-2 text-green-600">
                              <CheckCircle className="h-3 w-3" />
                              <span className="text-xs">
                                Completed: {formatDate(resolution.completedTime)}
                              </span>
                            </div>
                          )}

                          {!resolution.completedTime && (
                            <div>
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-muted-foreground">SLA Deadline</span>
                                <span
                                  className={
                                    slaStatus.isBreached
                                      ? "text-red-600 font-medium"
                                      : slaStatus.status === "at_risk"
                                      ? "text-orange-600 font-medium"
                                      : "text-green-600"
                                  }
                                >
                                  {slaStatus.isBreached
                                    ? "Overdue"
                                    : `${slaStatus.hoursLeft.toFixed(1)}h left`}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <div
                                  className={`h-1.5 rounded-full ${
                                    slaStatus.isBreached
                                      ? "bg-red-600"
                                      : slaStatus.status === "at_risk"
                                      ? "bg-orange-600"
                                      : "bg-green-600"
                                  }`}
                                  style={{
                                    width: slaStatus.isBreached
                                      ? "100%"
                                      : `${Math.min(100, ((24 - slaStatus.hoursLeft) / 24) * 100)}%`,
                                  }}
                                />
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Notes */}
                        {resolution.notes.length > 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <div className="text-xs font-medium text-muted-foreground mb-2">
                              Latest Notes:
                            </div>
                            <div className="space-y-1">
                              {resolution.notes.slice(-2).map((note, idx) => (
                                <div key={idx} className="text-xs text-muted-foreground">
                                  • {note}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Status Indicator */}
                        <div className="mt-3 pt-3 border-t flex items-center gap-2">
                          {resolution.status === "completed" && (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          )}
                          {resolution.status === "failed" && (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                          {resolution.status === "in_progress" && (
                            <div className="flex items-center gap-2">
                              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                              <span className="text-xs text-muted-foreground">
                                In Progress
                              </span>
                            </div>
                          )}
                          {resolution.status === "pending" && (
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-orange-600" />
                              <span className="text-xs text-muted-foreground">
                                Awaiting Action
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Status Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Resolutions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Anomaly ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Action Type
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Assigned To
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Notes
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    SLA Deadline
                  </th>
                </tr>
              </thead>
              <tbody>
                {resolutions.map((resolution) => (
                  <tr key={resolution.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-3 text-sm font-mono">{resolution.anomalyId}</td>
                    <td className="px-4 py-3 text-sm">
                      <Badge className={getActionTypeColor(resolution.actionType)}>
                        {resolution.actionType}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm">{resolution.assignedTo}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={resolution.status} />
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="text-muted-foreground">
                        {resolution.notes.length} notes
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-xs">
                      {formatDate(resolution.slaDeadline)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
