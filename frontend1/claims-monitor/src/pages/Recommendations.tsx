import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal } from "../components/ui/Modal";
import { Input } from "../components/ui/Input";
import { getRecommendations, getKnowledgeBase, searchKnowledgeBase } from "../services/api";
import { Lightbulb, BookOpen, Search, TrendingUp } from "lucide-react";
import type { Recommendation, KnowledgeBaseItem } from "../types";

export function Recommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedKBItem, setSelectedKBItem] = useState<KnowledgeBaseItem | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [recsData, kbData] = await Promise.all([
      getRecommendations(),
      getKnowledgeBase(),
    ]);
    setRecommendations(recsData);
    setKnowledgeBase(kbData);
  };

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      const results = await searchKnowledgeBase(searchQuery);
      setKnowledgeBase(results);
    } else {
      const allItems = await getKnowledgeBase();
      setKnowledgeBase(allItems);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Recommended Actions (RAG)</h1>
        <p className="text-muted-foreground mt-1">
          AI-generated recommendations and knowledge base references
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recommendations.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              High Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {recommendations.filter((r) => r.confidence >= 90).length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              KB Articles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{knowledgeBase.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(recommendations.reduce((sum, r) => sum + r.confidence, 0) / recommendations.length).toFixed(0)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recommendations by Action Type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {["Fix Data", "Reprocess", "Escalate", "Contact Team"].map((actionType) => {
          const recs = recommendations.filter((r) => r.actionType === actionType);
          if (recs.length === 0) return null;

          return (
            <Card key={actionType}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  {actionType} ({recs.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recs.map((rec) => (
                    <div
                      key={rec.id}
                      className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm mb-1">{rec.description}</h4>
                          <p className="text-xs text-muted-foreground">
                            Anomaly ID: {rec.anomalyId}
                          </p>
                        </div>
                        <div className="ml-3 flex flex-col gap-1">
                          <Badge variant="success">
                            {rec.confidence}% confidence
                          </Badge>
                          <Badge variant="info">
                            {rec.relevanceScore}% relevant
                          </Badge>
                        </div>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <BookOpen className="h-3 w-3" />
                          <span className="text-xs">SOP: {rec.sopReference}</span>
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <TrendingUp className="h-3 w-3" />
                          <span className="text-xs">Estimated Effort: {rec.estimatedEffort}</span>
                        </div>
                      </div>

                      {rec.steps && rec.steps.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-medium mb-1">Recommended Steps:</p>
                          <ol className="list-decimal list-inside text-xs text-muted-foreground space-y-1">
                            {rec.steps.slice(0, 3).map((step, idx) => (
                              <li key={idx}>{step}</li>
                            ))}
                            {rec.steps.length > 3 && (
                              <li className="text-primary cursor-pointer">
                                +{rec.steps.length - 3} more steps...
                              </li>
                            )}
                          </ol>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Knowledge Base */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Knowledge Base
          </CardTitle>
          <CardDescription>
            Search SOPs, business rules, policies, and past resolutions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search */}
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search knowledge base..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Search
            </button>
          </div>

          {/* KB Items Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {knowledgeBase.map((item) => (
              <div
                key={item.id}
                className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedKBItem(item)}
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-sm">{item.title}</h4>
                  <Badge
                    variant={
                      item.category === "SOP"
                        ? "info"
                        : item.category === "Business Rule"
                        ? "warning"
                        : item.category === "Policy"
                        ? "error"
                        : "default"
                    }
                  >
                    {item.category}
                  </Badge>
                </div>
                
                <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                  {item.content}
                </p>

                <div className="flex flex-wrap gap-1 mb-2">
                  {item.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-muted text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Referenced {item.relevanceCount} times</span>
                  <span>{new Date(item.lastUpdated).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* KB Item Detail Modal */}
      {selectedKBItem && (
        <Modal
          isOpen={!!selectedKBItem}
          onClose={() => setSelectedKBItem(null)}
          title={selectedKBItem.title}
          size="lg"
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  selectedKBItem.category === "SOP"
                    ? "info"
                    : selectedKBItem.category === "Business Rule"
                    ? "warning"
                    : selectedKBItem.category === "Policy"
                    ? "error"
                    : "default"
                }
              >
                {selectedKBItem.category}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Last updated: {new Date(selectedKBItem.lastUpdated).toLocaleDateString()}
              </span>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm whitespace-pre-wrap">{selectedKBItem.content}</p>
            </div>

            <div>
              <h4 className="text-sm font-medium mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {selectedKBItem.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                Referenced in {selectedKBItem.relevanceCount} recommendations
              </span>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
