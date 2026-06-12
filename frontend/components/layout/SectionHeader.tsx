import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  date?: string;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, date, action, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex items-baseline justify-between mb-6", className)}>
      <span className="text-[11px] uppercase tracking-[2px] text-muted-foreground font-semibold">
        {title}
      </span>
      <div className="flex items-center gap-4">
        {date && <span className="text-sm text-muted-foreground">{date}</span>}
        {action}
      </div>
    </div>
  );
}
