import Link from "next/link";
import { cn } from "@/lib/utils";

interface CourseListItemProps {
  num: string;
  name: string;
  chapter: string;
  percent: number;
  href?: string;
  className?: string;
}

export function CourseListItem({ num, name, chapter, percent, href, className }: CourseListItemProps) {
  const content = (
    <>
      <span className="font-mono text-[11px] text-muted-foreground w-6">{num}</span>
      <div>
        <div className="text-[15px] font-medium">{name}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{chapter}</div>
      </div>
      <div className="w-[100px] h-[3px] bg-border relative">
        <div
          className="absolute left-0 top-0 bottom-0 bg-foreground"
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="font-mono text-[13px] font-semibold w-10 text-right">{percent}%</span>
    </>
  );

  const baseClass = cn(
    "grid grid-cols-[auto_1fr_auto_auto] items-center gap-5 px-8 py-5 border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors",
    className,
  );

  if (href) {
    return (
      <Link href={href} className={cn(baseClass, "cursor-pointer")}>
        {content}
      </Link>
    );
  }

  return <div className={baseClass}>{content}</div>;
}
