import { Search, Bell, User, LogOut, Shield } from "lucide-react";
import { Input } from "../ui/Input";
import { useState } from "react";
import { useAuth } from "../../auth/AuthContext";

export function TopBar() {
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [notificationCount] = useState(3);

  return (
    <header className="bg-card border-b border-border px-6 py-3 sticky top-0 z-40">
      <div className="flex items-center justify-between">
        {/* Search */}
        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search claims anomalies, authorizations, rules, audit logs..."
              className="pl-10 text-xs font-mono"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3 ml-4">
          {/* Notifications */}
          <button
            className="relative p-2 hover:bg-accent rounded-md transition-colors text-muted-foreground hover:text-foreground"
            title="Notifications"
          >
            <Bell className="h-4 w-4" />
            {notificationCount > 0 && (
              <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-destructive text-destructive-foreground text-[9px] font-bold flex items-center justify-center rounded-full">
                {notificationCount}
              </span>
            )}
          </button>

          {/* User Menu Profile */}
          <div className="flex items-center gap-2.5 pl-2 border-l border-border">
            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary border border-primary/30 flex items-center justify-center font-bold text-xs">
              {user?.name ? user.name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
            </div>
            <div className="text-left hidden md:block">
              <p className="text-xs font-bold font-sans text-foreground leading-tight">
                {user?.name || "Healthcare Operator"}
              </p>
              <p className="text-[10px] font-mono text-muted-foreground flex items-center gap-1">
                {user?.role === "admin" ? (
                  <span className="text-blue-400 font-bold flex items-center gap-0.5">
                    <Shield className="w-2.5 h-2.5" /> Admin
                  </span>
                ) : (
                  <span className="text-cyan-400 font-bold">Data Steward</span>
                )}
              </p>
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              className="p-1.5 ml-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
