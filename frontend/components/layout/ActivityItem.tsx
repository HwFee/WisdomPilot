import { cn } from "@/lib/utils";

interface ActivityItemProps {
  time: string;
  title: React.ReactNode;
  meta?: string;
  className?: string;
}

export function ActivityItem({ time, title, meta, className }: ActivityItemProps) {
  return (
    <div className={cn("flex gap-4 px-8 py-4 border-b border-border last:border-b-0", className)}>
      <span className="font-mono text-xs text-muted-foreground w-16 text-right shrink-0 pt-0.5">
        {time}
      </span>
      <div className="flex-1 pl-4 border-l-2 border-border">
        <div className="text-sm">{title}</div>
        {meta && <div className="text-xs text-muted-foreground mt-1">{meta}</div>}
      </div>
    </div>
  );
}
