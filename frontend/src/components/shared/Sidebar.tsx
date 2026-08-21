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
  Cpu,
  Users,
  History,
  Briefcase,
  Shield,
  Bell,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useStore } from "../../store/useStore";
import { useAuth } from "../../auth/AuthContext";

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useStore();
  const { user, isAdmin } = useAuth();

  // Admin sees full platform config & ML engines; Worker sees operational tasks
  const adminNavigation = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Data Sources", href: "/data-sources", icon: Database },
    { name: "Quality Checks", href: "/quality-checks", icon: CheckCircle },
    { name: "Anomalies", href: "/anomalies", icon: AlertTriangle },
    { name: "ML Anomaly Engine", href: "/ml-engine", icon: Cpu },
    { name: "SLA & Priority", href: "/sla", icon: Clock },
    { name: "Recommendations", href: "/recommendations", icon: Lightbulb },
    { name: "Human Review", href: "/review", icon: UserCheck },
    { name: "Execute Actions", href: "/resolutions", icon: PlayCircle },
    { name: "Audit Trail", href: "/audit-trail", icon: History },
    { name: "Workers", href: "/workers", icon: Users },
    { name: "Notifications (SMTP)", href: "/notifications", icon: Bell },
    { name: "Monitoring", href: "/monitoring", icon: BarChart3 },
    { name: "Feedback", href: "/feedback", icon: MessageSquare },
  ];

  const workerNavigation = [
    { name: "My Work Queue", href: "/", icon: Briefcase },
    { name: "Anomalies", href: "/anomalies", icon: AlertTriangle },
    { name: "Recommendations", href: "/recommendations", icon: Lightbulb },
    { name: "Human Review", href: "/review", icon: UserCheck },
    { name: "Execute Actions", href: "/resolutions", icon: PlayCircle },
    { name: "Audit Trail", href: "/audit-trail", icon: History },
    { name: "Feedback", href: "/feedback", icon: MessageSquare },
  ];

  const activeNav = isAdmin ? adminNavigation : workerNavigation;

  return (
    <aside
      className={cn(
        "bg-card border-r border-border h-screen sticky top-0 transition-all duration-300 flex flex-col z-30",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-sm">
              <AlertTriangle className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-tight">Claims Monitor</h1>
              <p className="text-[10px] font-mono text-muted-foreground">
                {isAdmin ? "Admin Console" : "Operator Portal"}
              </p>
            </div>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 hover:bg-accent rounded-md transition-colors text-muted-foreground"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation list */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {activeNav.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-xs font-mono transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground font-bold shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                sidebarCollapsed && "justify-center"
              )
            }
            title={sidebarCollapsed ? item.name : undefined}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {!sidebarCollapsed && <span>{item.name}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer Role Badge */}
      <div className="p-3 border-t border-border bg-muted/20">
        {!sidebarCollapsed ? (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[10px]">
              {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="flex-1 truncate">
              <p className="text-xs font-bold truncate text-foreground">{user?.name || "Operator"}</p>
              <p className="text-[10px] font-mono text-muted-foreground flex items-center gap-1">
                {isAdmin ? (
                  <span className="text-blue-400 font-bold flex items-center gap-0.5">
                    <Shield className="w-2.5 h-2.5" /> Administrator
                  </span>
                ) : (
                  <span className="text-cyan-400 font-bold">Data Steward</span>
                )}
              </p>
            </div>
          </div>
        ) : (
          <div className="text-[10px] font-mono text-center text-muted-foreground">
            {isAdmin ? "ADM" : "WRK"}
          </div>
        )}
      </div>
    </aside>
  );
}
