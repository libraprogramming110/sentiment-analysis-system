import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { api, useApi, EMPTY_SUMMARY } from "@/lib/api"

export function SentimentDonut() {
  const { data: summary } = useApi(api.summary, EMPTY_SUMMARY, [])

  const total = summary.total || 1
  const distribution = [
    { name: "Positive", value: summary.positive, color: "hsl(var(--sentiment-positive))" },
    { name: "Neutral",  value: summary.neutral,  color: "hsl(var(--sentiment-neutral))"  },
    { name: "Negative", value: summary.negative, color: "hsl(var(--sentiment-negative))" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Overall Sentiment</CardTitle>
        <CardDescription>Distribution across {summary.total} reviews</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 items-center gap-6 sm:grid-cols-[auto_1fr]">
          <div className="relative mx-auto aspect-square w-44 sm:w-40 lg:w-44">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <Pie
                  data={distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius="62%"
                  outerRadius="92%"
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                  isAnimationActive={false}
                >
                  {distribution.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-semibold tabular-nums">
                {Math.round((summary.positive / total) * 100)}%
              </span>
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Positive</span>
            </div>
          </div>
          <div className="space-y-3">
            {distribution.map((s) => {
              const pct = Math.round((s.value / total) * 100)
              return (
                <div key={s.name}>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                      <span className="text-foreground">{s.name}</span>
                    </div>
                    <span className="tabular-nums text-muted-foreground">{s.value} <span className="text-xs">({pct}%)</span></span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: s.color }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
