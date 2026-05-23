import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { ReactNode } from "react"

interface StatCardProps {
  label: string
  value: ReactNode
  icon?: ReactNode
  tone?: "default" | "positive" | "negative" | "neutral" | "brand"
  helper?: string
}

const toneClass: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default:  "bg-card",
  positive: "bg-sentiment-positive/5 ring-sentiment-positive/10",
  negative: "bg-sentiment-negative/5 ring-sentiment-negative/10",
  neutral:  "bg-sentiment-neutral/5 ring-sentiment-neutral/10",
  brand:    "bg-brand/5 ring-brand/10",
}

const iconToneClass: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default:  "bg-muted text-foreground",
  positive: "bg-sentiment-positive/15 text-sentiment-positive",
  negative: "bg-sentiment-negative/15 text-sentiment-negative",
  neutral:  "bg-sentiment-neutral/15 text-sentiment-neutral",
  brand:    "bg-brand/15 text-brand",
}

export function StatCard({ label, value, icon, tone = "default", helper }: StatCardProps) {
  return (
    <Card className={cn("relative overflow-hidden ring-1 ring-border", toneClass[tone])}>
      <div className="flex items-start justify-between gap-3 p-5">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-semibold tracking-tight tabular-nums">{value}</span>
          </div>
          {helper && <p className="mt-1.5 text-xs text-muted-foreground">{helper}</p>}
        </div>
        {icon && (
          <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-lg", iconToneClass[tone])}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}
