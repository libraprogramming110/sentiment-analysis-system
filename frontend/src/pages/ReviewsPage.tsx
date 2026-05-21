import { useMemo, useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { reviews as fallbackReviews, type Sentiment, type Aspect, type Language } from "@/lib/mockData"
import { api, useApi, type ApiReview } from "@/lib/api"
import { ChevronDown, Download, Filter, Search, Star } from "lucide-react"
import { cn } from "@/lib/utils"

const sentimentLabel: Record<Sentiment, string> = { positive: "Positive", neutral: "Neutral", negative: "Negative" }
const langLabel: Record<string, string> = { en: "English", tl: "Filipino", ceb: "Cebuano", ilo: "Ilocano" }
const langFlag: Record<string, string>  = { en: "🇬🇧", tl: "🇵🇭", ceb: "🇵🇭", ilo: "🇵🇭" }
const aspectIcon: Record<Aspect, string> = { food: "🍽️", service: "🛎️", ambiance: "🪴", price: "₱", cleanliness: "✨" }

export function ReviewsPage() {
  const [q, setQ] = useState("")
  const [sentiment, setSentiment] = useState<Sentiment | "all">("all")
  const [aspect, setAspect] = useState<Aspect | "all">("all")
  const [lang, setLang] = useState<Language | "all">("all")
  const [expanded, setExpanded] = useState<number | null>(null)

  // Server-side filtering via the typed client.
  const { data, loading } = useApi(
    () => api.reviews({ sentiment, aspect, lang, q: q || undefined, limit: 200 }),
    { reviews: fallbackReviews as unknown as ApiReview[], total: fallbackReviews.length },
    [sentiment, aspect, lang, q],
  )

  const filtered = useMemo(
    () => (data.reviews.length || !loading ? data.reviews : (fallbackReviews as unknown as ApiReview[])),
    [data, loading],
  )

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card className="p-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by review text, evidence, or keyword…"
              className="pl-9"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Select value={sentiment} onValueChange={(v) => setSentiment(v as never)}>
              <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sentiment</SelectItem>
                <SelectItem value="positive">Positive</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
                <SelectItem value="negative">Negative</SelectItem>
              </SelectContent>
            </Select>
            <Select value={aspect} onValueChange={(v) => setAspect(v as never)}>
              <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All aspects</SelectItem>
                <SelectItem value="food">Food</SelectItem>
                <SelectItem value="service">Service</SelectItem>
                <SelectItem value="ambiance">Ambiance</SelectItem>
                <SelectItem value="price">Price</SelectItem>
                <SelectItem value="cleanliness">Cleanliness</SelectItem>
              </SelectContent>
            </Select>
            <Select value={lang} onValueChange={(v) => setLang(v as never)}>
              <SelectTrigger className="w-[140px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All languages</SelectItem>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="tl">Filipino</SelectItem>
                <SelectItem value="ceb">Cebuano</SelectItem>
                <SelectItem value="ilo">Ilocano</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Filter className="h-3.5 w-3.5" />
              More
            </Button>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Download className="h-3.5 w-3.5" />
              Export
            </Button>
          </div>
        </div>
      </Card>

      {/* Results meta */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          Showing <span className="font-medium text-foreground">{filtered.length}</span> results
          {loading && <span className="ml-2 opacity-60">loading…</span>}
        </span>
        <span>Sorted by date · newest first</span>
      </div>

      {/* Review list */}
      <div className="space-y-2">
        {filtered.map((r) => {
          const open = expanded === r.id
          return (
            <Card key={r.id} className="overflow-hidden transition-all hover:border-primary/30">
              <button
                type="button"
                onClick={() => setExpanded(open ? null : r.id)}
                className="w-full text-left"
              >
                <div className="flex items-start gap-4 p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-accent text-xs font-semibold text-white">
                    {(r.author ?? "?").split(" ").map((n) => n[0]).join("")}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium">{r.author}</span>
                      <span className="flex items-center gap-0.5 text-xs text-amber-500">
                        {Array.from({ length: r.rating || 0 }).map((_, i) => (
                          <Star key={i} className="h-3 w-3 fill-current" />
                        ))}
                      </span>
                      <Badge variant="outline" className="h-5 gap-1 px-1.5 text-[10px]">
                        <span>{langFlag[r.language] ?? "🏳️"}</span>
                        {langLabel[r.language] ?? r.language}
                      </Badge>
                      <Badge
                        variant={r.overall === "positive" ? "positive" : r.overall === "negative" ? "negative" : "neutral"}
                        className="h-5 px-1.5 text-[10px]"
                      >
                        {sentimentLabel[r.overall]}
                      </Badge>
                      <span className="ml-auto text-xs text-muted-foreground">{r.date}</span>
                    </div>

                    <p className="mt-1.5 text-sm leading-snug text-foreground">{r.originalText}</p>

                    {r.translatedText && (
                      <p className="mt-1 text-xs italic text-muted-foreground">
                        EN: {r.translatedText}
                      </p>
                    )}

                    <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                      {r.aspects.map((a) => (
                        <TooltipProvider key={a.aspect} delayDuration={150}>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Badge
                                variant={a.sentiment === "positive" ? "positive" : a.sentiment === "negative" ? "negative" : "neutral"}
                                className="h-5 cursor-help gap-1 px-1.5 text-[10px] capitalize"
                              >
                                <span>{aspectIcon[a.aspect]}</span>
                                {a.aspect}
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p className="text-[11px] font-medium uppercase tracking-wider opacity-70">Evidence</p>
                              <p className="mt-0.5 text-xs">"{a.evidence}"</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      ))}
                      <ChevronDown
                        className={cn(
                          "ml-auto h-4 w-4 text-muted-foreground transition-transform",
                          open && "rotate-180"
                        )}
                      />
                    </div>
                  </div>
                </div>
              </button>

              {open && (
                <div className="border-t bg-muted/30 px-4 py-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Aspect breakdown
                  </p>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    {r.aspects.map((a) => (
                      <div key={a.aspect} className="flex items-start gap-2 rounded-md border bg-background p-2.5">
                        <span className="text-base leading-none">{aspectIcon[a.aspect]}</span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium capitalize">{a.aspect}</span>
                            <Badge
                              variant={a.sentiment === "positive" ? "positive" : a.sentiment === "negative" ? "negative" : "neutral"}
                              className="h-4 px-1.5 text-[10px]"
                            >
                              {a.sentiment}
                            </Badge>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground italic">"{a.evidence}"</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )
        })}
        {!loading && filtered.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-sm text-muted-foreground">No reviews match these filters.</p>
          </Card>
        )}
      </div>
    </div>
  )
}
