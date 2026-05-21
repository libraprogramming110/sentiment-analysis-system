import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { aspectBreakdown as fallback } from "@/lib/mockData"
import { api, useApi } from "@/lib/api"
import { cn } from "@/lib/utils"

const aspectIcon: Record<string, string> = {
  food: "🍽️", service: "🛎️", ambiance: "🪴", price: "₱", cleanliness: "✨",
}

export function AspectBars() {
  const { data } = useApi(api.aspects, { aspects: fallback }, [])
  const rows = data.aspects.length ? data.aspects : fallback

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Aspect-Based Sentiment</CardTitle>
        <CardDescription>How customers feel about each part of the experience</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map((row) => {
          const total = (row.positive ?? 0) + (row.neutral ?? 0) + (row.negative ?? 0) || 1
          const pct = (n: number) => (n / total) * 100
          return (
            <div key={row.aspect}>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 capitalize">
                  <span className="text-base leading-none">{aspectIcon[row.aspect]}</span>
                  <span className="font-medium">{row.aspect}</span>
                  <span className="text-xs text-muted-foreground">{total} mentions</span>
                </div>
                <div className="flex items-center gap-3 text-xs tabular-nums">
                  <span className="text-sentiment-positive">+{row.positive}</span>
                  <span className="text-sentiment-neutral">·{row.neutral}</span>
                  <span className="text-sentiment-negative">−{row.negative}</span>
                </div>
              </div>
              <div className={cn("flex h-2.5 w-full overflow-hidden rounded-full bg-muted")}>
                <div className="bg-sentiment-positive transition-all" style={{ width: `${pct(row.positive)}%` }} />
                <div className="bg-sentiment-neutral transition-all"  style={{ width: `${pct(row.neutral)}%`  }} />
                <div className="bg-sentiment-negative transition-all" style={{ width: `${pct(row.negative)}%` }} />
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
