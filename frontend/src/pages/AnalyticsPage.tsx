import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { api, useApi } from "@/lib/api"
import { AspectIcon } from "@/components/widgets/AspectIcon"
import { BarChart3 } from "lucide-react"
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ScatterChart, Scatter, ZAxis
} from "recharts"

function EmptyState({ label }: { label: string }) {
  return (
    <Card className="p-12 text-center text-sm text-muted-foreground">{label}</Card>
  )
}

// Net-sentiment → 0..100 health score. Maps [-1,1] to [0,100]; always clamped.
function healthScore(positive: number, neutral: number, negative: number): number {
  const total = positive + neutral + negative || 1
  const net = (positive - negative) / total            // -1 .. 1
  return Math.max(0, Math.min(100, Math.round(((net + 1) / 2) * 100)))
}

export function AnalyticsPage() {
  const { data: aspectsResp } = useApi(api.aspects, { aspects: [] }, [])
  const aspectBreakdown = aspectsResp.aspects

  const { data: kwResp } = useApi(() => api.keywords(40), { keywords: [] }, [])
  const topKeywords = kwResp.keywords

  const { data: revResp } = useApi(() => api.reviews({ limit: 400 }), { reviews: [], total: 0 }, [])
  const reviewsData = revResp.reviews

  const radarData = aspectBreakdown.map((row) => ({
    aspect: row.aspect,
    score: healthScore(row.positive, row.neutral, row.negative),
  }))

  const posMax = Math.max(1, ...topKeywords.filter((k) => k.sentiment === "positive").map((k) => k.count))
  const negMax = Math.max(1, ...topKeywords.filter((k) => k.sentiment === "negative").map((k) => k.count))

  const ratingScatter = reviewsData.map((r) => ({
    rating: r.rating,
    sentimentScore: r.overall === "positive" ? 1 : r.overall === "neutral" ? 0 : -1,
    z: ((r.aspects?.length ?? 1) * 60),
  }))

  return (
    <Tabs defaultValue="aspects" className="space-y-4">
      <TabsList>
        <TabsTrigger value="aspects">Aspect Performance</TabsTrigger>
        <TabsTrigger value="keywords">Keyword Insights</TabsTrigger>
        <TabsTrigger value="rating">Rating vs Sentiment</TabsTrigger>
        <TabsTrigger value="evaluation">Pipeline Evaluation</TabsTrigger>
      </TabsList>

      {/* Aspect Performance */}
      <TabsContent value="aspects" className="space-y-4">
        {aspectBreakdown.length === 0 && <EmptyState label="No aspect data yet." />}
        {aspectBreakdown.length > 0 && (
        <>
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Aspect Volume Comparison</CardTitle>
              <CardDescription>Positive vs negative mentions per aspect</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={aspectBreakdown} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="aspect" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
                    <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)", fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="positive" fill="hsl(var(--sentiment-positive))" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="neutral"  fill="hsl(var(--sentiment-neutral))"  radius={[4, 4, 0, 0]} />
                    <Bar dataKey="negative" fill="hsl(var(--sentiment-negative))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Aspect Health Score</CardTitle>
              <CardDescription>Net sentiment per aspect (0–100)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="hsl(var(--border))" />
                    <PolarAngleAxis dataKey="aspect" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                    <PolarRadiusAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} angle={90} domain={[0, 100]} />
                    <Radar dataKey="score" stroke="hsl(var(--brand))" fill="hsl(var(--brand))" fillOpacity={0.25} />
                    <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)", fontSize: 12 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {aspectBreakdown.map((row) => {
            const total = row.positive + row.neutral + row.negative || 1
            const score = healthScore(row.positive, row.neutral, row.negative)
            return (
              <Card key={row.aspect} className="overflow-hidden">
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <AspectIcon aspect={row.aspect} className="h-6 w-6 text-2xl text-muted-foreground" />
                    <Badge variant={score >= 70 ? "positive" : score >= 50 ? "neutral" : "negative"}>{score}/100</Badge>
                  </div>
                  <p className="mt-3 text-sm font-medium capitalize">{row.aspect}</p>
                  <p className="text-xs text-muted-foreground">{total} mentions</p>
                </div>
                <div className="flex h-1 w-full">
                  <div className="bg-sentiment-positive" style={{ width: `${(row.positive / total) * 100}%` }} />
                  <div className="bg-sentiment-neutral"  style={{ width: `${(row.neutral  / total) * 100}%` }} />
                  <div className="bg-sentiment-negative" style={{ width: `${(row.negative / total) * 100}%` }} />
                </div>
              </Card>
            )
          })}
        </div>
        </>
        )}
      </TabsContent>

      {/* Keywords */}
      <TabsContent value="keywords" className="space-y-4">
        {topKeywords.length === 0 && <EmptyState label="No keyword data yet." />}
        {topKeywords.length > 0 && (
        <>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top Positive Keywords</CardTitle>
              <CardDescription>Most-mentioned praise terms</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {topKeywords.filter((k) => k.sentiment === "positive").slice(0, 8).map((k) => (
                <div key={k.word} className="flex items-center gap-3">
                  <span className="w-24 truncate text-sm font-medium">{k.word}</span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-sentiment-positive" style={{ width: `${(k.count / posMax) * 100}%` }} />
                  </div>
                  <span className="w-10 text-right text-xs tabular-nums text-muted-foreground">{k.count}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top Negative Keywords</CardTitle>
              <CardDescription>Most-mentioned complaint terms</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {topKeywords.filter((k) => k.sentiment === "negative").slice(0, 8).map((k) => (
                <div key={k.word} className="flex items-center gap-3">
                  <span className="w-24 truncate text-sm font-medium">{k.word}</span>
                  <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-sentiment-negative" style={{ width: `${(k.count / negMax) * 100}%` }} />
                  </div>
                  <span className="w-10 text-right text-xs tabular-nums text-muted-foreground">{k.count}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Keyword Cloud</CardTitle>
            <CardDescription>Sized by frequency, colored by sentiment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center justify-center gap-3 py-6">
              {topKeywords.slice(0, 28).map((k) => {
                const fontSize = 14 + Math.min(28, Math.floor(k.count / 3))
                const color =
                  k.sentiment === "positive" ? "hsl(var(--sentiment-positive))" :
                  k.sentiment === "negative" ? "hsl(var(--sentiment-negative))" :
                  "hsl(var(--sentiment-neutral))"
                return (
                  <span
                    key={k.word}
                    className="font-semibold transition-transform hover:scale-110"
                    style={{ fontSize, color }}
                  >
                    {k.word}
                  </span>
                )
              })}
            </div>
          </CardContent>
        </Card>
        </>
        )}
      </TabsContent>

      {/* Rating vs Sentiment */}
      <TabsContent value="rating">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Rating vs Sentiment Alignment</CardTitle>
            <CardDescription>Does the star rating match what the customer actually wrote?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 16, right: 16, left: -8, bottom: 0 }}>
                  <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="rating" name="Rating" domain={[0, 6]} tickCount={7}
                    tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false}
                    label={{ value: "Star rating", position: "insideBottom", offset: -2, fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis type="number" dataKey="sentimentScore" name="Sentiment" domain={[-1.5, 1.5]} ticks={[-1, 0, 1]}
                    tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false}
                    tickFormatter={(v) => (v === 1 ? "Pos" : v === 0 ? "Neu" : v === -1 ? "Neg" : "")} />
                  <ZAxis type="number" dataKey="z" range={[60, 220]} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)", fontSize: 12 }} />
                  <Scatter data={ratingScatter} fill="hsl(var(--brand))" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Mismatches (e.g. 5★ but negative sentiment) flag reviews where the rating disagrees with the text — useful for spotting sarcasm or ambiguous feedback.
            </p>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Pipeline Evaluation */}
      <TabsContent value="evaluation" className="space-y-4">
        <EvaluationPanel />
      </TabsContent>
    </Tabs>
  )
}

function EvaluationPanel() {
  const { data, loading } = useApi(
    api.evaluation,
    { vader: {}, hybrid: {}, _pending: true } as { vader: Record<string, number>; hybrid: Record<string, number>; _pending?: boolean },
    [],
  )

  if (loading) {
    return <Card className="p-12 text-center text-sm text-muted-foreground">Loading evaluation…</Card>
  }

  const pending = data._pending || !Object.keys(data.hybrid).length
  if (pending) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><BarChart3 className="h-4 w-4" /> Pipeline Evaluation</CardTitle>
          <CardDescription>Hybrid (LLM) vs VADER baseline — not yet run.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed bg-muted/30 p-8 text-center">
            <p className="text-sm font-medium">Evaluation pending</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Run the evaluation harness (hand-label 50 reviews, then{" "}
              <code className="rounded bg-muted px-1 py-0.5 font-mono">python evaluation/evaluate.py</code>)
              to populate the accuracy comparison here.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const compareData = Object.keys(data.hybrid).map((k) => ({
    metric: k,
    "VADER baseline": data.vader[k] ?? 0,
    "Hybrid (LLM)": data.hybrid[k] ?? 0,
  }))

  return (
    <Card className="border-brand/30 bg-brand/[0.02]">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <BarChart3 className="h-4 w-4" /> Pipeline Comparison: Hybrid (LLM) vs VADER Baseline
        </CardTitle>
        <CardDescription>
          Empirical justification for the hybrid NLP architecture — measured on hand-labeled reviews.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={compareData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} width={40} />
              <Tooltip contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: "var(--radius)", fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="VADER baseline" fill="hsl(var(--sentiment-neutral))" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Hybrid (LLM)"   fill="hsl(var(--brand))"             radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border bg-background p-3">
            <p className="text-xs text-muted-foreground">VADER baseline</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums">{data.vader.overall ?? 0}%</p>
            <p className="text-xs text-muted-foreground">Overall accuracy</p>
          </div>
          <div className="rounded-lg border border-brand/30 bg-brand/5 p-3">
            <p className="text-xs text-muted-foreground">Hybrid (LLM)</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-brand">{data.hybrid.overall ?? 0}%</p>
            <p className="text-xs text-muted-foreground">Overall accuracy</p>
          </div>
          <div className="rounded-lg border border-sentiment-positive/30 bg-sentiment-positive/5 p-3">
            <p className="text-xs text-muted-foreground">Improvement</p>
            <p className="mt-1 text-2xl font-semibold tabular-nums text-sentiment-positive">
              +{(data.hybrid.overall ?? 0) - (data.vader.overall ?? 0)}%
            </p>
            <p className="text-xs text-muted-foreground">delta vs baseline</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
