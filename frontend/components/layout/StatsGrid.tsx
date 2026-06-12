import { cn } from "@/lib/utils";

interface StatsGridProps {
  children: React.ReactNode;
  className?: string;
}

export function StatsGrid({ children, className }: StatsGridProps) {
  return (
    <div className={cn("grid grid-cols-2 lg:grid-cols-4 gap-[1px] bg-border", className)}>
      {children}
    </div>
  );
}

export function StatCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("bg-card p-8", className)}>{children}</div>;
}
