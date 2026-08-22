import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Database, CheckCircle, AlertTriangle, Clock,
  Lightbulb, UserCheck, PlayCircle, BarChart3, MessageSquare,
  ChevronLeft, ChevronRight, LogOut, Users,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useStore } from "../../store/useStore";
import { useAuth } from "../../auth/AuthContext";
import { useEffect, useState } from "react";
import api from "../../services/api";

const navigation = [
  { name: "Overview",       href: "/admin/dashboard",      icon: LayoutDashboard, badge: 0 },
  { name: "Data Sources",   href: "/admin/data-sources",   icon: Database,        badge: 0 },
  { name: "Quality Checks", href: "/admin/quality",        icon: CheckCircle,     badge: 0 },
  { name: "Anomalies",      href: "/admin/anomalies",      icon: AlertTriangle,   badge: 0 },
  { name: "SLA & Priority", href: "/admin/sla",            icon: Clock,           badge: 0 },
  { name: "Recommendations",href: "/admin/recommendations", icon: Lightbulb,      badge: 0 },
  { name: "Human Review",   href: "/admin/review",         icon: UserCheck,       badge: -1 }, // -1 = dynamic
  { name: "Execute Actions",href: "/admin/resolutions",    icon: PlayCircle,      badge: -2 }, // -2 = dynamic
  { name: "Monitoring",     href: "/admin/monitoring",     icon: BarChart3,       badge: 0 },
  { name: "Feedback",       href: "/admin/feedback",       icon: MessageSquare,   badge: 0 },
  { name: "Workers",        href: "/admin/workers",        icon: Users,           badge: 0 },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useStore();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Live badge counts
  const [pendingReviews, setPendingReviews] = useState(0);
  const [openActions,    setOpenActions]    = useState(0);

  useEffect(() => {
    const load = () => {
      api.get("/reviews?status=pending_review&page_size=1")
         .then(r => setPendingReviews(Array.isArray(r.data) ? r.data.length : 0))
         .catch(() => {});
      api.get("/actions?status=created")
         .then(r => setOpenActions(Array.isArray(r.data) ? r.data.length : 0))
         .catch(() => {});
    };
    load();
    const interval = setInterval(load, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <aside
      className={cn(
        "bg-card border-r border-border h-screen sticky top-0 transition-all duration-300 flex flex-col",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand */}
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
          {sidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navigation.map(({ name, href, icon: Icon, badge }) => {
          // Resolve dynamic badge counts
          const liveBadge = badge === -1 ? pendingReviews
                          : badge === -2 ? openActions
                          : badge;
          return (
            <NavLink
              key={name}
              to={href}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  sidebarCollapsed && "justify-center"
                )
              }
              title={sidebarCollapsed ? name : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1">{name}</span>
                  {liveBadge > 0 && (
                    <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-red-500 text-white min-w-[18px] text-center leading-none">
                      {liveBadge > 99 ? "99+" : liveBadge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="p-3 border-t border-border space-y-1">
        {!sidebarCollapsed && (
          <div className="px-3 py-2">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        )}
        <button
          onClick={() => { logout(); navigate("/login", { replace: true }); }}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:bg-red-50 hover:text-red-600",
            sidebarCollapsed && "justify-center"
          )}
          title={sidebarCollapsed ? "Logout" : undefined}
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {!sidebarCollapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
