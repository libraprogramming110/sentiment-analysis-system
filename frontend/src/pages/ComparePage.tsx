import { useMemo, useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api, useApi, type RestaurantRow } from "@/lib/api"
import { Star, Trophy, MapPin, Info } from "lucide-react"
import {
  Tooltip as UiTooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from "recharts"
import { cn } from "@/lib/utils"

// Minimum reviews before a score is considered fully "credible". Below this,
// the Bayesian-adjusted score shrinks toward the global average.
const CREDIBILITY_M = 20
const SMALL_SAMPLE_THRESHOLD = 15
// Original scraped cities sort first; any uploaded cities follow alphabetically.
const KNOWN_CITY_ORDER = ["Cagayan de Oro", "Iligan City", "Marawi City"]

function rawHealth(r: RestaurantRow): number {
  const total = r.positive + r.neutral + r.negative || 1
  const net = (r.positive - r.negative) / total
  return Math.max(0, Math.min(100, Math.round(((net + 1) / 2) * 100)))
}

function positivePct(r: RestaurantRow): number {
  const total = r.positive + r.neutral + r.negative || 1
  return Math.round((r.positive / total) * 100)
}

export function ComparePage() {
  const { data, loading } = useApi(api.restaurants, { restaurants: [] }, [])
  const [cityFilter, setCityFilter] = useState<string>("all")

  const all = useMemo(() => data.restaurants.filter((r) => r.reviews > 0), [data])

  // Global average raw-health across ALL restaurants (the Bayesian prior).
  const globalAvg = useMemo(() => {
    if (!all.length) return 50
    return all.reduce((s, r) => s + rawHealth(r), 0) / all.length
  }, [all])

  // Bayesian-adjusted score (IMDb-style): credible scores survive, thin ones
  // get pulled toward the global average.
  const adjusted = (r: RestaurantRow) => {
    const v = r.reviews
    const R = rawHealth(r)
    return (v / (v + CREDIBILITY_M)) * R + (CREDIBILITY_M / (v + CREDIBILITY_M)) * globalAvg
  }

  const visible = cityFilter === "all" ? all : all.filter((r) => r.city === cityFilter)
  const ranked = [...visible].sort((a, b) => adjusted(b) - adjusted(a))

  // Cities present in the data: known scraped ones first, then any uploaded ones.
  const cityNames = useMemo(() => {
    const present = [...new Set(all.map((r) => r.city).filter(Boolean))] as string[]
    const known = KNOWN_CITY_ORDER.filter((c) => present.includes(c))
    const extra = present.filter((c) => !KNOWN_CITY_ORDER.includes(c)).sort()
    return [...known, ...extra]
  }, [all])

  const cities = cityNames.map((city) => {
    const group = all.filter((r) => r.city === city)
    const totals = group.reduce(
      (acc, r) => ({
        reviews: acc.reviews + r.reviews,
        positive: acc.positive + r.positive,
        neutral: acc.neutral + r.neutral,
        negative: acc.negative + r.negative,
        ratingSum: acc.ratingSum + r.avg_rating * r.reviews,
      }),
      { reviews: 0, positive: 0, neutral: 0, negative: 0, ratingSum: 0 },
    )
    const total = totals.positive + totals.neutral + totals.negative || 1
    return {
      city,
      count: group.length,
      reviews: totals.reviews,
      posPct: Math.round((totals.positive / total) * 100),
      avgRating: totals.reviews ? +(totals.ratingSum / totals.reviews).toFixed(2) : 0,
    }
  }).filter((c) => c.reviews > 0)

  const chartData = ranked.map((r) => ({
    name: r.name.length > 18 ? r.name.slice(0, 17) + "…" : r.name,
    positive: positivePct(r),
  }))

  if (loading) {
    return <Card className="p-12 text-center text-sm text-muted-foreground">Loading restaurants…</Card>
  }

  const filterTabs = ["all", ...cityNames]

  return (
    <div className="space-y-6">
      {/* City filter */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Filter:</span>
        {filterTabs.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setCityFilter(c)}
            className={cn(
              "rounded-md border px-3 py-1.5 text-xs font-medium transition-colors",
              cityFilter === c
                ? "border-brand bg-brand/10 text-brand"
                : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {c === "all" ? "All Cities" : c}
          </button>
        ))}
        <span className="ml-auto text-xs text-muted-foreground">
          {visible.length} {visible.length === 1 ? "restaurant" : "restaurants"}
        </span>
      </div>

      {/* City summary cards — one per city present in the data */}
      <div className="grid gap-4 sm:grid-cols-3">
        {cities.map((c) => (
          <Card
            key={c.city}
            className={cn(
              "cursor-pointer transition-colors",
              cityFilter === c.city && "border-brand ring-1 ring-brand/30"
            )}
            onClick={() => setCityFilter(cityFilter === c.city ? "all" : c.city)}
          >
            <CardContent className="p-5">
              <div className="flex items-center gap-2 text-sm font-medium">
                <MapPin className="h-4 w-4 text-brand" />
                {c.city}
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-semibold tabular-nums">{c.posPct}%</span>
                <span className="text-xs text-muted-foreground">positive</span>
              </div>
              <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                <span>{c.count} restaurants</span>
                <span>·</span>
                <span>{c.reviews} reviews</span>
                <span>·</span>
                <span className="inline-flex items-center gap-0.5">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> {c.avgRating}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Comparison chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Positive Sentiment by Restaurant</CardTitle>
          <CardDescription>
            Ranked by credibility-adjusted score
            {cityFilter !== "all" ? ` · ${cityFilter}` : ` · all ${cityNames.length} cities`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div style={{ height: Math.max(220, chartData.length * 42) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
                <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} unit="%" />
                <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11, fill: "hsl(var(--foreground))" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)", fontSize: 12 }} />
                <Bar dataKey="positive" radius={[0, 4, 4, 0]} unit="%">
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.positive >= 80 ? "hsl(var(--sentiment-positive))" : d.positive >= 60 ? "hsl(var(--brand))" : "hsl(var(--sentiment-negative))"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Leaderboard table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Trophy className="h-4 w-4 text-amber-500" />
            Restaurant Leaderboard
          </CardTitle>
          <CardDescription className="flex items-center gap-1.5">
            Ranked by credibility-adjusted health score
            <TooltipProvider delayDuration={150}>
              <UiTooltip>
                <TooltipTrigger asChild>
                  <Info className="h-3.5 w-3.5 cursor-help text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-xs">
                    Uses Bayesian shrinkage (the IMDb method): restaurants with few reviews are
                    pulled toward the average until they earn their rank, so a 9-review place can't
                    out-rank a 50-review one on luck.
                  </p>
                </TooltipContent>
              </UiTooltip>
            </TooltipProvider>
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">#</th>
                  <th className="px-4 py-2.5 font-medium">Restaurant</th>
                  <th className="px-4 py-2.5 font-medium">City</th>
                  <th className="px-4 py-2.5 font-medium text-right">Reviews</th>
                  <th className="px-4 py-2.5 font-medium text-right">Rating</th>
                  <th className="px-4 py-2.5 font-medium">Sentiment</th>
                  <th className="px-4 py-2.5 font-medium text-right">Health</th>
                </tr>
              </thead>
              <tbody>
                {ranked.map((r, i) => {
                  const total = r.positive + r.neutral + r.negative || 1
                  const score = rawHealth(r)
                  const adj = Math.round(adjusted(r))
                  const small = r.reviews < SMALL_SAMPLE_THRESHOLD
                  return (
                    <tr key={r.restaurant_id} className="border-b last:border-0 transition-colors hover:bg-muted/40">
                      <td className="px-4 py-3 tabular-nums text-muted-foreground">{i + 1}</td>
                      <td className="px-4 py-3 font-medium">
                        <div className="flex items-center gap-2">
                          {r.name}
                          {small && (
                            <Badge variant="secondary" className="h-4 px-1.5 text-[9px] font-normal">
                              small sample
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{r.city}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{r.reviews}</td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        <span className="inline-flex items-center gap-0.5">
                          <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> {r.avg_rating}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex h-2 w-32 overflow-hidden rounded-full bg-muted">
                          <div className="bg-sentiment-positive" style={{ width: `${(r.positive / total) * 100}%` }} />
                          <div className="bg-sentiment-neutral"  style={{ width: `${(r.neutral  / total) * 100}%` }} />
                          <div className="bg-sentiment-negative" style={{ width: `${(r.negative / total) * 100}%` }} />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex flex-col items-end gap-0.5">
                          <Badge variant={adj >= 70 ? "positive" : adj >= 50 ? "neutral" : "negative"}>
                            {adj}/100
                          </Badge>
                          {small && (
                            <span className="text-[9px] text-muted-foreground tabular-nums">raw {score}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
