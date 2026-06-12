import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn("max-w-[1280px] mx-auto px-6 lg:px-12", className)}>
      {children}
    </div>
  );
}
