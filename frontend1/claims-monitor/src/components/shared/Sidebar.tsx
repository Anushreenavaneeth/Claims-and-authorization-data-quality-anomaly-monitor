import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Database,
  CheckCircle,
  AlertTriangle,
  Clock,
  Lightbulb,
  UserCheck,
  PlayCircle,
  BarChart3,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useStore } from "../../store/useStore";

const navigation = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Data Sources", href: "/data-sources", icon: Database },
  { name: "Quality Checks", href: "/quality-checks", icon: CheckCircle },
  { name: "Anomalies", href: "/anomalies", icon: AlertTriangle },
  { name: "SLA & Priority", href: "/sla", icon: Clock },
  { name: "Recommendations", href: "/recommendations", icon: Lightbulb },
  { name: "Human Review", href: "/review", icon: UserCheck },
  { name: "Execute Actions", href: "/resolutions", icon: PlayCircle },
  { name: "Monitoring", href: "/monitoring", icon: BarChart3 },
  { name: "Feedback", href: "/feedback", icon: MessageSquare },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useStore();

  return (
    <aside
      className={cn(
        "bg-card border-r border-border h-screen sticky top-0 transition-all duration-300 flex flex-col",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-bold text-sm">Claims Monitor</h1>
              <p className="text-xs text-muted-foreground">Data Quality</p>
            </div>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1 hover:bg-accent rounded-md transition-colors"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                sidebarCollapsed && "justify-center"
              )
            }
            title={sidebarCollapsed ? item.name : undefined}
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {!sidebarCollapsed && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        {!sidebarCollapsed ? (
          <div className="text-xs text-muted-foreground">
            <p>Version 1.0.0</p>
            <p className="mt-1">© 2026 Claims Monitor</p>
          </div>
        ) : (
          <div className="text-xs text-muted-foreground text-center">v1.0</div>
        )}
      </div>
    </aside>
  );
}
