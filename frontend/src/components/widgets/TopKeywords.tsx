import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { topKeywords as fallback } from "@/lib/mockData"
import { api, useApi } from "@/lib/api"
import { TrendingUp } from "lucide-react"

export function TopKeywords() {
  const { data } = useApi(() => api.keywords(20), { keywords: fallback }, [])
  const rows = data.keywords.length ? data.keywords : fallback

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-brand" />
          Trending Keywords
        </CardTitle>
        <CardDescription>Most-mentioned words across reviews this period</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {rows.map((k, i) => {
            const fontSize = 13 + Math.min(8, Math.floor(k.count / 12))
            return (
              <Badge
                key={k.word}
                variant={k.sentiment === "positive" ? "positive" : k.sentiment === "negative" ? "negative" : "neutral"}
                className="gap-1.5 px-2.5 py-1"
                style={{ fontSize }}
              >
                <span className="font-medium">{k.word}</span>
                <span className="text-[10px] opacity-70 tabular-nums">{k.count}</span>
                {i === 0 && <span className="ml-0.5 text-[9px] uppercase tracking-wider opacity-70">top</span>}
              </Badge>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
