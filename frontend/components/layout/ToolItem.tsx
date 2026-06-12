import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToolItemProps {
  icon: React.ReactNode;
  iconClassName?: string;
  name: string;
  desc: string;
  onClick?: () => void;
  className?: string;
}

export function ToolItem({ icon, iconClassName, name, desc, onClick, className }: ToolItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-4 px-8 py-4 border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors text-left",
        className
      )}
    >
      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center shrink-0", iconClassName)}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[15px] font-medium">{name}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{desc}</div>
      </div>
      <ChevronRight className="w-5 h-5 text-muted-foreground" />
    </button>
  );
}
