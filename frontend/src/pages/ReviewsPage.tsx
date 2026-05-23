import { useEffect, useMemo, useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { type Sentiment, type Aspect, type Language } from "@/lib/mockData"
import { api, useApi, type ApiReview } from "@/lib/api"
import { ChevronDown, ChevronLeft, ChevronRight, Search, Star, Store } from "lucide-react"
import { AspectIcon } from "@/components/widgets/AspectIcon"
import { UploadDialog } from "@/components/widgets/UploadDialog"
import { langLabel } from "@/lib/languages"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 15

const sentimentLabel: Record<Sentiment, string> = { positive: "Positive", neutral: "Neutral", negative: "Negative" }

const EMPTY: { reviews: ApiReview[]; total: number } = { reviews: [], total: 0 }

export function ReviewsPage() {
  const [q, setQ] = useState("")
  const [sentiment, setSentiment] = useState<Sentiment | "all">("all")
  const [aspect, setAspect] = useState<Aspect | "all">("all")
  const [lang, setLang] = useState<Language | "all">("all")
  const [restaurantId, setRestaurantId] = useState<number | "all">("all")
  const [expanded, setExpanded] = useState<number | null>(null)
  // Bumped after a successful CSV upload to force the lists below to refetch.
  const [refreshKey, setRefreshKey] = useState(0)

  // Restaurant list for the filter dropdown (grouped by city below).
  const { data: restoData } = useApi(api.restaurants, { restaurants: [] }, [refreshKey])
  const restaurants = restoData.restaurants.filter((r) => r.reviews > 0)

  // Languages present in the data → drives the language filter (adapts to uploads).
  const { data: langData } = useApi(api.languages, { languages: [] }, [refreshKey])
  const languageCodes = langData.languages.map((l) => l.lang).filter(Boolean)

  // Server-side filtering via the typed client. Empty fallback (not mock data)
  // so the page shows a skeleton while loading instead of flashing fake reviews.
  const { data, loading, error } = useApi(
    () => api.reviews({ sentiment, aspect, lang, q: q || undefined, restaurantId, limit: 500 }),
    EMPTY,
    [sentiment, aspect, lang, q, restaurantId, refreshKey],
  )

  const filtered = data.reviews

  // Pagination
  const [page, setPage] = useState(1)
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  // Reset to page 1 whenever the filtered set changes (new filter/search).
  useEffect(() => { setPage(1) }, [sentiment, aspect, lang, q, restaurantId])
  const safePage = Math.min(page, pageCount)
  const pageItems = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  // Group restaurants by city for the dropdown.
  const byCity = useMemo(() => {
    const m = new Map<string, typeof restaurants>()
    for (const r of restaurants) {
      const c = r.city ?? "Other"
      if (!m.has(c)) m.set(c, [])
      m.get(c)!.push(r)
    }
    // Keep cities alphabetical, but always push the "Other" group (no city,
    // e.g. uploaded restaurants) to the bottom.
    return [...m.entries()].sort(([a], [b]) => {
      if (a === "Other") return 1
      if (b === "Other") return -1
      return a.localeCompare(b)
    })
  }, [restaurants])

  const anyFilter = sentiment !== "all" || aspect !== "all" || lang !== "all" || restaurantId !== "all" || !!q
  const showSkeleton = loading && filtered.length === 0

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
            <Select
              value={String(restaurantId)}
              onValueChange={(v) => setRestaurantId(v === "all" ? "all" : Number(v))}
            >
              <SelectTrigger className="w-[190px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All restaurants</SelectItem>
                {byCity.map(([city, list]) => (
                  <SelectGroup key={city}>
                    <SelectLabel>{city}</SelectLabel>
                    {list.map((r) => (
                      <SelectItem key={r.restaurant_id} value={String(r.restaurant_id)}>
                        {r.name}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>
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
                {languageCodes.map((code) => (
                  <SelectItem key={code} value={code}>{langLabel(code)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <UploadDialog onUploaded={() => setRefreshKey((k) => k + 1)} />
          </div>
        </div>
      </Card>

      {/* Results meta */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {anyFilter
            ? <>Showing <span className="font-medium text-foreground">{filtered.length}</span> matching reviews</>
            : <>Showing all <span className="font-medium text-foreground">{filtered.length}</span> reviews</>}
          {loading && <span className="ml-2 opacity-60">loading…</span>}
        </span>
        <span>
          {filtered.length > 0 && (
            <>Showing {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} · newest first</>
          )}
        </span>
      </div>

      {/* Loading skeleton — shown instead of mock data so there's no flash */}
      {showSkeleton && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-start gap-4">
                <div className="h-9 w-9 shrink-0 animate-pulse rounded-full bg-muted" />
                <div className="flex-1 space-y-2">
                  <div className="h-3.5 w-40 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-full animate-pulse rounded bg-muted" />
                  <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Error state */}
      {!loading && error && filtered.length === 0 && (
        <Card className="p-12 text-center">
          <p className="text-sm text-muted-foreground">
            Couldn't load reviews — is the backend running on port 5000?
          </p>
        </Card>
      )}

      {/* Review list */}
      <div className="space-y-2">
        {!showSkeleton && pageItems.map((r) => {
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
                        {langLabel(r.language)}
                      </Badge>
                      <Badge
                        variant={r.overall === "positive" ? "positive" : r.overall === "negative" ? "negative" : "neutral"}
                        className="h-5 px-1.5 text-[10px]"
                      >
                        {sentimentLabel[r.overall]}
                      </Badge>
                      <Badge variant="secondary" className="h-5 gap-1 px-1.5 text-[10px] font-normal">
                        <Store className="h-3 w-3" />
                        {r.restaurantName}
                        {r.city && <span className="opacity-60">· {r.city}</span>}
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
                                <AspectIcon aspect={a.aspect} className="h-3 w-3 text-[10px]" />
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
                        <AspectIcon aspect={a.aspect} className="h-4 w-4 text-base text-muted-foreground" />
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
        {!loading && !error && filtered.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-sm text-muted-foreground">No reviews match these filters.</p>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {pageCount > 1 && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Page <span className="font-medium text-foreground">{safePage}</span> of {pageCount}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline" size="sm" className="gap-1"
              disabled={safePage <= 1}
              onClick={() => { setExpanded(null); setPage((p) => Math.max(1, p - 1)) }}
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Prev
            </Button>
            {pageWindow(safePage, pageCount).map((p, i) =>
              p === "…" ? (
                <span key={`gap-${i}`} className="px-1.5 text-xs text-muted-foreground">…</span>
              ) : (
                <Button
                  key={p}
                  variant={p === safePage ? "default" : "outline"}
                  size="sm"
                  className="h-8 w-8 p-0 tabular-nums"
                  onClick={() => { setExpanded(null); setPage(p as number) }}
                >
                  {p}
                </Button>
              )
            )}
            <Button
              variant="outline" size="sm" className="gap-1"
              disabled={safePage >= pageCount}
              onClick={() => { setExpanded(null); setPage((p) => Math.min(pageCount, p + 1)) }}
            >
              Next <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

/** Compact page-number window with ellipses, e.g. [1, …, 4, 5, 6, …, 26]. */
function pageWindow(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | "…")[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  if (start > 2) pages.push("…")
  for (let p = start; p <= end; p++) pages.push(p)
  if (end < total - 1) pages.push("…")
  pages.push(total)
  return pages
}
