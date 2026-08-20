import { getStatusColor, getSeverityColor, getPriorityColor } from "../../lib/utils";
import { cn } from "../../lib/utils";

interface StatusBadgeProps {
  status: string;
  type?: "status" | "severity" | "priority";
  className?: string;
}

export function StatusBadge({ status, type = "status", className }: StatusBadgeProps) {
  let colorClass = "";
  
  if (type === "severity") {
    // If status is a number (severity score), use it directly
    const severity = typeof status === "number" ? status : parseInt(status);
    if (!isNaN(severity)) {
      colorClass = getSeverityColor(severity);
    }
  } else if (type === "priority") {
    colorClass = getPriorityColor(status);
  } else {
    colorClass = getStatusColor(status);
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        colorClass,
        className
      )}
    >
      {status}
    </span>
  );
}
