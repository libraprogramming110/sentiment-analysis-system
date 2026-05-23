/**
 * Typed Flask API client.
 *
 * - Reads VITE_API_BASE from env (defaults to http://127.0.0.1:5000)
 * - One thin fetch helper, one typed function per endpoint
 * - Throws on non-2xx so callers can do try/catch and fall back to mockData
 */
import type { Aspect, Language, Sentiment } from "./mockData"

// In production the SPA is served by Flask on the same origin, so call "/api/..."
// relatively. In dev, hit the local Flask server. An explicit VITE_API_BASE wins either way.
const BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.PROD ? "" : "http://127.0.0.1:5000")

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { Accept: "application/json" } })
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json() as Promise<T>
}

// ────────────────────────────────────────────────────────────────────────────
// Response types — must mirror backend/db/repo.py output shapes
// ────────────────────────────────────────────────────────────────────────────
export interface SummaryResponse {
  total: number
  positive: number
  neutral: number
  negative: number
  avgRating: number
}

export interface TrendPoint { day: string; positive: number; neutral: number; negative: number }
export interface AspectRow  { aspect: Aspect; positive: number; neutral: number; negative: number }
export interface Issue      { issue: string; mentions: number; aspect: Aspect }
export interface LangRow    { lang: Language; count: number }
export interface KeywordRow { word: string; count: number; sentiment: Sentiment }

export interface RestaurantRow {
  restaurant_id: number
  name: string
  city: string | null
  reviews: number
  avg_rating: number
  positive: number
  neutral: number
  negative: number
}

export interface ApiReview {
  id: number
  restaurantId: number
  restaurantName: string
  city: string | null
  author: string
  rating: number
  language: Language
  date: string
  originalText: string
  translatedText: string | null
  overall: Sentiment
  aspects: { aspect: Aspect; sentiment: Sentiment; evidence: string }[]
}

export interface AnalyzeRequest  { text: string }
export interface AnalyzeResponse {
  language: string
  overall_sentiment: Sentiment
  overall_confidence: number
  aspects: { aspect: Aspect; sentiment: Sentiment; evidence: string }[]
  keywords: string[]
}

// ────────────────────────────────────────────────────────────────────────────
// Endpoints
// ────────────────────────────────────────────────────────────────────────────
export const api = {
  health:      ()                    => get<{ status: string; groq_key_loaded: boolean }>("/api/health"),
  restaurants: ()                    => get<{ restaurants: RestaurantRow[] }>("/api/restaurants"),
  summary:    ()                     => get<SummaryResponse>("/api/summary"),
  trend:      ()                     => get<{ trend: TrendPoint[] }>("/api/trend"),
  issues:     ()                     => get<{ issues: Issue[]      }>("/api/issues"),
  languages:  ()                     => get<{ languages: LangRow[] }>("/api/languages"),
  aspects:    ()                     => get<{ aspects: AspectRow[] }>("/api/aspects"),
  keywords:   (limit = 20)           => get<{ keywords: KeywordRow[] }>(`/api/keywords?limit=${limit}`),
  evaluation: ()                     => get<{ vader: Record<string, number>; hybrid: Record<string, number>; _pending?: boolean }>("/api/evaluation"),
  reviews:    (params: {
    sentiment?:     Sentiment | "all"
    aspect?:        Aspect    | "all"
    lang?:          Language  | "all"
    q?:             string
    restaurantId?:  number    | "all"
    limit?:         number
  } = {}) => {
    const qs = new URLSearchParams()
    if (params.sentiment && params.sentiment !== "all") qs.set("sentiment", params.sentiment)
    if (params.aspect    && params.aspect    !== "all") qs.set("aspect", params.aspect)
    if (params.lang      && params.lang      !== "all") qs.set("lang", params.lang)
    if (params.q)                                      qs.set("q", params.q)
    if (params.restaurantId && params.restaurantId !== "all") qs.set("restaurant_id", String(params.restaurantId))
    if (params.limit)                                  qs.set("limit", String(params.limit))
    const qstr = qs.toString()
    return get<{ reviews: ApiReview[]; total: number }>(`/api/reviews${qstr ? `?${qstr}` : ""}`)
  },
  analyze: (body: AnalyzeRequest) => post<AnalyzeResponse>("/api/analyze", body),
}

// ────────────────────────────────────────────────────────────────────────────
// React hook for one-shot fetches with loading + graceful fallback
// ────────────────────────────────────────────────────────────────────────────
import { useEffect, useState } from "react"

export function useApi<T>(fn: () => Promise<T>, fallback: T, deps: unknown[] = []) {
  const [data, setData]       = useState<T>(fallback)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fn()
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e: Error) => {
        if (!cancelled) { setError(e); setData(fallback) }
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error }
}
