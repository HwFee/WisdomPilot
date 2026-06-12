import { cn } from "@/lib/utils";

interface PanelProps {
  children: React.ReactNode;
  className?: string;
}

interface PanelHeaderProps {
  title: string;
  count?: string;
  action?: React.ReactNode;
  className?: string;
}

export function Panel({ children, className }: PanelProps) {
  return (
    <div className={cn("bg-card border border-border", className)}>
      {children}
    </div>
  );
}

export function PanelHeader({ title, count, action, className }: PanelHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between px-8 py-6 border-b border-border", className)}>
      <span className="text-[13px] font-semibold uppercase tracking-[1.5px]">{title}</span>
      <div className="flex items-center gap-4">
        {count ? <span className="font-mono text-[13px] text-muted-foreground">{count}</span> : null}
        {action}
      </div>
    </div>
  );
}
