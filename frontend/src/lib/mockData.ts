// Placeholder data so the UI looks alive before the Flask backend is wired.
// Shape mirrors the API contracts in starter.MD §8.

export type Sentiment = "positive" | "neutral" | "negative"
export type Aspect = "food" | "service" | "ambiance" | "price" | "cleanliness"
export type Language = "en" | "tl" | "ceb" | "ilo"

export const summary = {
  total: 287,
  positive: 174,
  neutral: 62,
  negative: 51,
  avgRating: 4.2,
}

export const sentimentDistribution = [
  { name: "Positive", value: summary.positive, color: "hsl(var(--sentiment-positive))" },
  { name: "Neutral",  value: summary.neutral,  color: "hsl(var(--sentiment-neutral))"  },
  { name: "Negative", value: summary.negative, color: "hsl(var(--sentiment-negative))" },
]

export const aspectBreakdown: { aspect: Aspect; positive: number; neutral: number; negative: number }[] = [
  { aspect: "food",        positive: 142, neutral: 28, negative: 17 },
  { aspect: "service",     positive: 88,  neutral: 41, negative: 53 },
  { aspect: "ambiance",    positive: 96,  neutral: 35, negative: 12 },
  { aspect: "price",       positive: 64,  neutral: 47, negative: 38 },
  { aspect: "cleanliness", positive: 81,  neutral: 22, negative: 9  },
]

export const trend = [
  { day: "Apr 09", positive: 18, neutral: 6, negative: 4 },
  { day: "Apr 13", positive: 22, neutral: 7, negative: 5 },
  { day: "Apr 17", positive: 19, neutral: 9, negative: 7 },
  { day: "Apr 21", positive: 26, neutral: 8, negative: 6 },
  { day: "Apr 25", positive: 28, neutral: 10, negative: 8 },
  { day: "Apr 29", positive: 24, neutral: 11, negative: 9 },
  { day: "May 03", positive: 32, neutral: 9,  negative: 7 },
  { day: "May 07", positive: 35, neutral: 12, negative: 5 },
]

export const topKeywords = [
  { word: "masarap",    count: 84, sentiment: "positive" as Sentiment },
  { word: "mabagal",    count: 47, sentiment: "negative" as Sentiment },
  { word: "ambiance",   count: 41, sentiment: "positive" as Sentiment },
  { word: "mahal",      count: 38, sentiment: "negative" as Sentiment },
  { word: "friendly",   count: 34, sentiment: "positive" as Sentiment },
  { word: "lami",       count: 29, sentiment: "positive" as Sentiment },
  { word: "crowded",    count: 22, sentiment: "negative" as Sentiment },
  { word: "fresh",      count: 19, sentiment: "positive" as Sentiment },
]

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

export const reviews: Review[] = [
  {
    id: 1, author: "Maria L.", rating: 5, language: "tl", date: "2026-05-08",
    originalText: "Sobrang masarap ang adobo at sinigang! Ang serbisyo naman ay friendly pero medyo mabagal kasi puno.",
    translatedText: "The adobo and sinigang are really delicious! The service is friendly but a bit slow because it's full.",
    overall: "positive",
    aspects: [
      { aspect: "food", sentiment: "positive", evidence: "Sobrang masarap ang adobo at sinigang" },
      { aspect: "service", sentiment: "negative", evidence: "medyo mabagal kasi puno" },
    ],
  },
  {
    id: 2, author: "John R.", rating: 4, language: "en", date: "2026-05-07",
    originalText: "Great ambiance and the staff are accommodating. Prices are a bit on the higher side though.",
    overall: "positive",
    aspects: [
      { aspect: "ambiance", sentiment: "positive", evidence: "Great ambiance" },
      { aspect: "service", sentiment: "positive", evidence: "staff are accommodating" },
      { aspect: "price", sentiment: "negative", evidence: "Prices are a bit on the higher side" },
    ],
  },
  {
    id: 3, author: "Cristina P.", rating: 2, language: "ceb", date: "2026-05-06",
    originalText: "Lami ang pagkaon pero hugaw ang lamesa ug dugay kaayo ang waiter mu-attend.",
    translatedText: "The food is tasty but the table was dirty and the waiter took very long to attend.",
    overall: "negative",
    aspects: [
      { aspect: "food", sentiment: "positive", evidence: "Lami ang pagkaon" },
      { aspect: "cleanliness", sentiment: "negative", evidence: "hugaw ang lamesa" },
      { aspect: "service", sentiment: "negative", evidence: "dugay kaayo ang waiter mu-attend" },
    ],
  },
  {
    id: 4, author: "Joseph M.", rating: 5, language: "ilo", date: "2026-05-05",
    originalText: "Naimas unay ti pinakbet ken nagsayaat ti serbisyo. Awan duduana, agsubliak.",
    translatedText: "The pinakbet was very delicious and the service was excellent. No doubt, I'll return.",
    overall: "positive",
    aspects: [
      { aspect: "food", sentiment: "positive", evidence: "Naimas unay ti pinakbet" },
      { aspect: "service", sentiment: "positive", evidence: "nagsayaat ti serbisyo" },
    ],
  },
  {
    id: 5, author: "Aliyah S.", rating: 3, language: "tl", date: "2026-05-04",
    originalText: "Okay lang ang food, walang kakaiba. Maingay sa loob, mahirap mag-usap.",
    translatedText: "The food is just okay, nothing special. It's noisy inside, hard to talk.",
    overall: "neutral",
    aspects: [
      { aspect: "food", sentiment: "neutral", evidence: "Okay lang ang food" },
      { aspect: "ambiance", sentiment: "negative", evidence: "Maingay sa loob" },
    ],
  },
  {
    id: 6, author: "Mark D.", rating: 5, language: "en", date: "2026-05-03",
    originalText: "Best lechon kawali I've ever had. Worth every peso. Will definitely come back!",
    overall: "positive",
    aspects: [
      { aspect: "food", sentiment: "positive", evidence: "Best lechon kawali I've ever had" },
      { aspect: "price", sentiment: "positive", evidence: "Worth every peso" },
    ],
  },
  {
    id: 7, author: "Reyna F.", rating: 1, language: "tl", date: "2026-05-02",
    originalText: "Ang baho ng banyo at madumi ang sahig. Hindi na ako babalik dito.",
    translatedText: "The bathroom smells bad and the floor is dirty. I won't come back here.",
    overall: "negative",
    aspects: [
      { aspect: "cleanliness", sentiment: "negative", evidence: "Ang baho ng banyo at madumi ang sahig" },
    ],
  },
  {
    id: 8, author: "Carlos U.", rating: 4, language: "en", date: "2026-05-01",
    originalText: "Solid Filipino food at fair prices. Ambiance is cozy. Service could be a bit faster.",
    overall: "positive",
    aspects: [
      { aspect: "food", sentiment: "positive", evidence: "Solid Filipino food" },
      { aspect: "price", sentiment: "positive", evidence: "fair prices" },
      { aspect: "ambiance", sentiment: "positive", evidence: "Ambiance is cozy" },
      { aspect: "service", sentiment: "negative", evidence: "Service could be a bit faster" },
    ],
  },
]

export const topIssues = [
  { issue: "Slow service during peak hours",   mentions: 47, aspect: "service" as Aspect },
  { issue: "Pricing perceived as too high",     mentions: 38, aspect: "price"   as Aspect },
  { issue: "Bathroom cleanliness complaints",   mentions: 19, aspect: "cleanliness" as Aspect },
]

export const pipelineComparison = {
  vader:  { overall: 71, food: 68, service: 64, ambiance: 70, price: 66, cleanliness: 73 },
  hybrid: { overall: 89, food: 91, service: 86, ambiance: 88, price: 84, cleanliness: 92 },
}

export const languageBreakdown = [
  { lang: "Filipino (tl)", count: 138, color: "hsl(var(--brand))" },
  { lang: "English (en)",  count: 92,  color: "hsl(var(--brand-accent))" },
  { lang: "Cebuano (ceb)", count: 38,  color: "hsl(280 80% 60%)" },
  { lang: "Ilocano (ilo)", count: 19,  color: "hsl(40 90% 55%)" },
]
