import { Search, Bell, User } from "lucide-react";
import { Input } from "../ui/Input";
import { useState } from "react";

export function TopBar() {
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
              placeholder="Search anomalies, sources, checks..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4 ml-4">
          {/* Notifications */}
          <button className="relative p-2 hover:bg-accent rounded-md transition-colors">
            <Bell className="h-5 w-5" />
            {notificationCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-destructive text-destructive-foreground text-xs flex items-center justify-center rounded-full">
                {notificationCount}
              </span>
            )}
          </button>

          {/* User Menu */}
          <button className="flex items-center gap-2 p-2 hover:bg-accent rounded-md transition-colors">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="text-left hidden md:block">
              <p className="text-sm font-medium">Admin User</p>
              <p className="text-xs text-muted-foreground">Analyst</p>
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}
