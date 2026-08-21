import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { getFeedback, submitFeedback } from "../services/api";
import { formatDate } from "../lib/utils";
import { MessageSquare, ThumbsUp, ThumbsDown, Send } from "lucide-react";
import type { Feedback } from "../types";

export function FeedbackPage() {
  const [feedbackItems, setFeedbackItems] = useState<Feedback[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    wasHelpful: true,
    comments: "",
    suggestedImprovement: "",
    category: "Recommendation Quality" as Feedback["category"],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFeedback();
  }, []);

  const loadFeedback = async () => {
    const data = await getFeedback();
    setFeedbackItems(data);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await submitFeedback({
        ...formData,
        anomalyId: undefined,
        recommendationId: undefined,
      });
      setFormData({
        wasHelpful: true,
        comments: "",
        suggestedImprovement: "",
        category: "Recommendation Quality",
      });
      setShowForm(false);
      await loadFeedback();
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    } finally {
      setLoading(false);
    }
  };

  const categoryColors = {
    "Recommendation Quality": "info",
    "Rule Improvement": "warning",
    "False Positive": "error",
    "Other": "default",
  } as const;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Feedback Loop</h1>
          <p className="text-muted-foreground mt-1">
            Share your insights to improve recommendations and detection rules
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <MessageSquare className="h-4 w-4 mr-2" />
          {showForm ? "Cancel" : "Submit Feedback"}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Feedback
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{feedbackItems.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Helpful
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ThumbsUp className="h-5 w-5 text-green-600" />
              <div className="text-2xl font-bold text-green-600">
                {feedbackItems.filter((f) => f.wasHelpful).length}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Not Helpful
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ThumbsDown className="h-5 w-5 text-red-600" />
              <div className="text-2xl font-bold text-red-600">
                {feedbackItems.filter((f) => !f.wasHelpful).length}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Improvement Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {feedbackItems.length > 0
                ? `${((feedbackItems.filter((f) => f.wasHelpful).length / feedbackItems.length) * 100).toFixed(1)}%`
                : "N/A"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feedback Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Submit New Feedback</CardTitle>
            <CardDescription>
              Help us improve the system by sharing your experience
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Was Helpful Toggle */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Was this recommendation helpful?
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, wasHelpful: true })}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md border transition-colors ${
                      formData.wasHelpful
                        ? "bg-green-50 border-green-500 text-green-700"
                        : "bg-background border-border"
                    }`}
                  >
                    <ThumbsUp className="h-4 w-4" />
                    Yes, Helpful
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, wasHelpful: false })}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md border transition-colors ${
                      !formData.wasHelpful
                        ? "bg-red-50 border-red-500 text-red-700"
                        : "bg-background border-border"
                    }`}
                  >
                    <ThumbsDown className="h-4 w-4" />
                    No, Not Helpful
                  </button>
                </div>
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  className="w-full px-3 py-2 border rounded-md"
                  value={formData.category}
                  onChange={(e) =>
                    setFormData({ ...formData, category: e.target.value as Feedback["category"] })
                  }
                >
                  <option value="Recommendation Quality">Recommendation Quality</option>
                  <option value="Rule Improvement">Rule Improvement</option>
                  <option value="False Positive">False Positive</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {/* Comments */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Comments <span className="text-red-600">*</span>
                </label>
                <textarea
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  rows={4}
                  placeholder="Share your feedback..."
                  value={formData.comments}
                  onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
                  required
                />
              </div>

              {/* Suggested Improvement */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Suggested Improvement (Optional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border rounded-md text-sm"
                  rows={3}
                  placeholder="How can we improve?"
                  value={formData.suggestedImprovement}
                  onChange={(e) =>
                    setFormData({ ...formData, suggestedImprovement: e.target.value })
                  }
                />
              </div>

              <Button type="submit" disabled={loading || !formData.comments.trim()}>
                <Send className="h-4 w-4 mr-2" />
                {loading ? "Submitting..." : "Submit Feedback"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Feedback Items */}
      <Card>
        <CardHeader>
          <CardTitle>All Feedback</CardTitle>
          <CardDescription>Review submitted feedback from the team</CardDescription>
        </CardHeader>
        <CardContent>
          {feedbackItems.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 text-muted-foreground/50" />
              <p>No feedback submitted yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {feedbackItems.map((item) => (
                <div key={item.id} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {item.wasHelpful ? (
                        <ThumbsUp className="h-5 w-5 text-green-600" />
                      ) : (
                        <ThumbsDown className="h-5 w-5 text-red-600" />
                      )}
                      <div>
                        <div className="font-medium">
                          {item.wasHelpful ? "Helpful" : "Not Helpful"}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          By {item.submittedBy} on {formatDate(item.submittedAt)}
                        </div>
                      </div>
                    </div>
                    <Badge variant={categoryColors[item.category]}>{item.category}</Badge>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <p className="text-sm">{item.comments}</p>
                    </div>

                    {item.suggestedImprovement && (
                      <div className="pt-2 border-t">
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          Suggested Improvement:
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {item.suggestedImprovement}
                        </p>
                      </div>
                    )}

                    {item.anomalyId && (
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground">
                          Related to Anomaly: <span className="font-mono">{item.anomalyId}</span>
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
