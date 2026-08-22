import { useAuth } from "../auth/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { CheckSquare, Activity, Wrench, RefreshCw } from "lucide-react";

const MODULES = [
  { icon: CheckSquare, label: "Assigned Tasks",  desc: "Tasks routed to you by severity and SLA deadline.",            tag: "queue"    },
  { icon: Activity,    label: "Task Status",     desc: "Move tasks through investigation → in-progress → resolved.",   tag: "status"   },
  { icon: Wrench,      label: "Remediation",     desc: "Submit corrective actions with evidence and resolution notes.", tag: "action"   },
  { icon: RefreshCw,   label: "Reprocessing",    desc: "Trigger re-ingestion and validation after fix confirmed.",     tag: "pipeline" },
];

export default function WorkerDashboard() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Worker · Dashboard</p>
        <h1 className="text-3xl font-bold">{user?.name?.split(" ")[0]}, ready to work.</h1>
        <p className="text-muted-foreground mt-1">Your task queue and remediation tools</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "Assigned Tasks",   value: "0", sub: "no tasks yet",      color: "text-blue-600" },
          { label: "Resolved Today",   value: "0", sub: "start remediating", color: "text-green-600" },
          { label: "Avg Resolution",   value: "—", sub: "no data yet",       color: "text-gray-600" },
        ].map(s => (
          <Card key={s.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{s.label}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{s.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Upcoming modules */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Modules</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            {MODULES.map((m, i) => (
              <div key={m.label} className="flex items-center gap-4 py-4">
                <span className="text-xl font-bold text-muted-foreground/30 w-8 tabular-nums">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center flex-shrink-0">
                  <m.icon className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold">{m.label}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{m.desc}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                    {m.tag}
                  </span>
                  <span className="text-xs text-muted-foreground">soon</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
