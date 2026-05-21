import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { trend as fallback } from "@/lib/mockData"
import { api, useApi } from "@/lib/api"
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts"

export function TrendChart() {
  const { data } = useApi(api.trend, { trend: fallback }, [])
  const raw = data.trend.length ? data.trend : fallback
  // Normalize day label — accept either ISO ("2026-05-16") or pre-formatted ("Apr 09")
  const rows = raw.map((r) => {
    const d = new Date(r.day)
    return {
      ...r,
      day: isNaN(d.getTime())
        ? r.day
        : d.toLocaleDateString("en-US", { month: "short", day: "2-digit" }),
    }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Sentiment Trend</CardTitle>
        <CardDescription>Volume of reviews per sentiment over the last 30 days</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={rows} margin={{ top: 10, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="g-pos" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"  stopColor="hsl(var(--sentiment-positive))" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="hsl(var(--sentiment-positive))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="g-neu" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"  stopColor="hsl(var(--sentiment-neutral))" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="hsl(var(--sentiment-neutral))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="g-neg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"  stopColor="hsl(var(--sentiment-negative))" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(var(--sentiment-negative))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--popover))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="positive" stroke="hsl(var(--sentiment-positive))" strokeWidth={2} fill="url(#g-pos)" />
              <Area type="monotone" dataKey="neutral"  stroke="hsl(var(--sentiment-neutral))"  strokeWidth={2} fill="url(#g-neu)" />
              <Area type="monotone" dataKey="negative" stroke="hsl(var(--sentiment-negative))" strokeWidth={2} fill="url(#g-neg)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
