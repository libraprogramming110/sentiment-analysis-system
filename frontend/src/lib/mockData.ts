// Shared domain types used across the UI and API client.
// (Mock data constants were removed — the app now reads everything live from the
// API and shows empty/zero states instead of fabricated numbers.)

export type Sentiment = "positive" | "neutral" | "negative"
export type Aspect = "food" | "service" | "ambiance" | "price" | "cleanliness"
// Known language codes; the detector may return others (handled by lib/languages.ts).
export type Language = "en" | "tl" | "ceb" | "ilo"

export interface Review {
  id: number
  author: string
  rating: number
  language: Language
  date: string
  originalText: string
  translatedText?: string
  overall: Sentiment
  aspects: { aspect: Aspect; sentiment: Sentiment; evidence: string }[]
}
