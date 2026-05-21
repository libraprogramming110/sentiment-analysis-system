import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { topIssues as fallback } from "@/lib/mockData"
import { api, useApi } from "@/lib/api"
import { AlertTriangle, ChevronRight } from "lucide-react"

export function TopIssues() {
  const { data } = useApi(api.issues, { issues: fallback }, [])
  const rows = data.issues.length ? data.issues : fallback

  return (
    <Card className="border-sentiment-negative/20 bg-sentiment-negative/[0.02]">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-sentiment-negative/15 text-sentiment-negative">
            <AlertTriangle className="h-4 w-4" />
          </span>
          Top 3 Issues Detected
        </CardTitle>
        <CardDescription>Auto-summarized concerns that need attention</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.map((issue, i) => (
          <div
            key={issue.issue}
            className="group flex items-center gap-3 rounded-md border bg-background p-3 transition-colors hover:bg-muted/50"
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sentiment-negative/15 text-xs font-semibold text-sentiment-negative">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{issue.issue}</p>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="outline" className="h-4 px-1.5 text-[10px] capitalize">
                  {issue.aspect}
                </Badge>
                <span>{issue.mentions} mentions</span>
              </div>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
