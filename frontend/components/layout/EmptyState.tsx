import Link from "next/link"
import { type LucideIcon } from "lucide-react"
import { Panel } from "./Panel"
import { Button } from "@/components/ui/button"

export interface EmptyStateAction {
  label: string
  href: string
}

export interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  primaryAction?: EmptyStateAction
  secondaryAction?: EmptyStateAction
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  primaryAction,
  secondaryAction,
}: EmptyStateProps) {
  return (
    <Panel>
      <div className="flex flex-col items-center justify-center text-center px-8 py-16">
        <div className="size-12 border border-border flex items-center justify-center mb-6">
          <Icon strokeWidth={1.5} className="size-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">{title}</h2>
        <p className="text-sm text-muted-foreground max-w-md mb-8 leading-relaxed">
          {description}
        </p>
        <div className="flex items-center gap-3">
          {primaryAction && (
            <Button asChild>
              <Link href={primaryAction.href}>{primaryAction.label}</Link>
            </Button>
          )}
          {secondaryAction && (
            <Button asChild variant="ghost">
              <Link href={secondaryAction.href}>{secondaryAction.label}</Link>
            </Button>
          )}
        </div>
      </div>
    </Panel>
  )
}
