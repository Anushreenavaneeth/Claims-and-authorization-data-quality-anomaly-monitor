import { cn } from "../../lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  const variantClasses = {
    default: "bg-gray-100 text-gray-800 border-gray-300",
    success: "bg-green-50 text-green-700 border-green-300",
    warning: "bg-yellow-50 text-yellow-700 border-yellow-300",
    error: "bg-red-50 text-red-700 border-red-300",
    info: "bg-blue-50 text-blue-700 border-blue-300",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
