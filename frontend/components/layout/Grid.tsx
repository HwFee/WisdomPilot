import { cn } from "@/lib/utils";

interface GridProps {
  children: React.ReactNode;
  className?: string;
}

export function Grid({ children, className }: GridProps) {
  return (
    <div className={cn("grid grid-cols-12 gap-6", className)}>
      {children}
    </div>
  );
}
