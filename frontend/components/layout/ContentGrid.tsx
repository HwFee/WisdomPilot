import { cn } from "@/lib/utils";

interface ContentGridProps {
  children: React.ReactNode;
  className?: string;
}

export function ContentGrid({ children, className }: ContentGridProps) {
  return (
    <div className={cn("grid grid-cols-1 lg:grid-cols-2 gap-12", className)}>
      {children}
    </div>
  );
}
