import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/shared/StatusBadge";
import { Modal } from "../components/ui/Modal";
import { Badge } from "../components/ui/Badge";
import { getReviewItems, approveAction, rejectAction } from "../services/api";
import { formatDate, getSeverityColor } from "../lib/utils";
import { CheckCircle, XCircle, Edit3, AlertTriangle } from "lucide-react";
import type { ReviewItem } from "../types";

export function Review() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null);
  const [actionModal, setActionModal] = useState<"approve" | "reject" | null>(null);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    const data = await getReviewItems();
    setItems(data);
  };

  const handleApprove = async () => {
    if (!selectedItem) return;
    setLoading(true);
    try {
      const updated = await approveAction(selectedItem.id, comment);
      setItems(items.map((item) => (item.id === updated.id ? updated : item)));
      setActionModal(null);
      setComment("");
      setSelectedItem(null);
    } catch (error) {
      console.error("Failed to approve:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedItem || !comment.trim()) {
      alert("Comment is required for rejection");
      return;
    }
    setLoading(true);
    try {
      const updated = await rejectAction(selectedItem.id, comment);
      setItems(items.map((item) => (item.id === updated.id ? updated : item)));
      setActionModal(null);
      setComment("");
      setSelectedItem(null);
    } catch (error) {
      console.error("Failed to reject:", error);
    } finally {
      setLoading(false);
    }
  };

  const pendingItems = items.filter((item) => item.status === "pending_review");
  const reviewedItems = items.filter((item) => item.status !== "pending_review");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Human Review Queue</h1>
        <p className="text-muted-foreground mt-1">
          Review anomalies and approve or modify recommended actions
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{pendingItems.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Approved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {items.filter((item) => item.status === "approved").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rejected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {items.filter((item) => item.status === "rejected").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Modified
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {items.filter((item) => item.status === "modified").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Review Items */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            Items Pending Review ({pendingItems.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {pendingItems.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-600" />
              <p>All items have been reviewed!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingItems.map((item) => (
                <div key={item.id} className="p-4 border rounded-lg">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Anomaly Summary */}
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        Anomaly Summary
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">ID:</span>{" "}
                          <span className="font-mono">{item.anomaly.id}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Type:</span>{" "}
                          <Badge variant="warning">{item.anomaly.anomalyType}</Badge>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Severity:</span>{" "}
                          <span className={`font-medium ${getSeverityColor(item.anomaly.severityScore)}`}>
                            {item.anomaly.severityScore}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Source:</span>{" "}
                          {item.anomaly.source}
                        </div>
                        <div>
                          <span className="text-muted-foreground">Detected:</span>{" "}
                          {formatDate(item.anomaly.detectedTime)}
                        </div>
                        <div>
                          <p className="text-muted-foreground">Description:</p>
                          <p className="mt-1">{item.anomaly.description}</p>
                        </div>
                      </div>
                    </div>

                    {/* Recommended Action */}
                    <div>
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        Recommended Action
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <Badge variant="info">{item.recommendation.actionType}</Badge>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Description:</p>
                          <p className="mt-1">{item.recommendation.description}</p>
                        </div>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          <div>
                            <span className="text-muted-foreground">Confidence:</span>{" "}
                            <Badge variant="success">{item.recommendation.confidence}%</Badge>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Effort:</span>{" "}
                            {item.recommendation.estimatedEffort}
                          </div>
                        </div>
                        <div>
                          <span className="text-muted-foreground">SOP Reference:</span>{" "}
                          <span className="text-xs">{item.recommendation.sopReference}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3 mt-4 pt-4 border-t">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => {
                        setSelectedItem(item);
                        setActionModal("approve");
                      }}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        setSelectedItem(item);
                        setActionModal("reject");
                      }}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit3 className="h-4 w-4 mr-2" />
                      Modify
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reviewed Items */}
      <Card>
        <CardHeader>
          <CardTitle>Reviewed Items ({reviewedItems.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {reviewedItems.length === 0 ? (
            <p className="text-center py-4 text-muted-foreground">No reviewed items yet</p>
          ) : (
            <div className="space-y-3">
              {reviewedItems.map((item) => (
                <div key={item.id} className="p-3 border rounded-lg flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{item.anomaly.anomalyType}</div>
                    <div className="text-xs text-muted-foreground">
                      {item.anomaly.id} | Reviewed by {item.reviewedBy} on{" "}
                      {item.reviewedAt && formatDate(item.reviewedAt)}
                    </div>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Modals */}
      {selectedItem && actionModal === "approve" && (
        <Modal
          isOpen={true}
          onClose={() => {
            setActionModal(null);
            setComment("");
          }}
          title="Approve Action"
        >
          <div className="space-y-4">
            <p className="text-sm">
              You are about to approve the recommended action for anomaly{" "}
              <span className="font-mono font-medium">{selectedItem.anomaly.id}</span>.
            </p>

            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Action to be executed:</p>
              <p className="text-sm mt-1">{selectedItem.recommendation.description}</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Optional Comment
              </label>
              <textarea
                className="w-full px-3 py-2 border rounded-md text-sm"
                rows={3}
                placeholder="Add any notes or comments..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
            </div>

            <div className="flex gap-3">
              <Button onClick={handleApprove} disabled={loading}>
                {loading ? "Processing..." : "Confirm Approval"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setActionModal(null);
                  setComment("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {selectedItem && actionModal === "reject" && (
        <Modal
          isOpen={true}
          onClose={() => {
            setActionModal(null);
            setComment("");
          }}
          title="Reject Action"
        >
          <div className="space-y-4">
            <p className="text-sm">
              You are about to reject the recommended action for anomaly{" "}
              <span className="font-mono font-medium">{selectedItem.anomaly.id}</span>.
            </p>

            <div>
              <label className="block text-sm font-medium mb-2">
                Rejection Reason <span className="text-red-600">*</span>
              </label>
              <textarea
                className="w-full px-3 py-2 border rounded-md text-sm"
                rows={4}
                placeholder="Explain why this action is not appropriate..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                required
              />
            </div>

            <div className="flex gap-3">
              <Button
                variant="danger"
                onClick={handleReject}
                disabled={loading || !comment.trim()}
              >
                {loading ? "Processing..." : "Confirm Rejection"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setActionModal(null);
                  setComment("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
