/**
 * Language display helpers. Unlike aspects (a fixed set the LLM is constrained to),
 * detected languages are open-ended — uploaded reviews can be in any language the
 * detector returns. These helpers give known languages a friendly name + brand color
 * and gracefully handle unknown codes (uppercased label + a stable generated color).
 */

const LABELS: Record<string, string> = {
  en: "English",
  tl: "Filipino",
  ceb: "Cebuano",
  ilo: "Ilocano",
  unknown: "Unknown",
  // common extras the detector might return for uploaded data
  es: "Spanish",
  fr: "French",
  de: "German",
  it: "Italian",
  pt: "Portuguese",
  id: "Indonesian",
  ms: "Malay",
  zh: "Chinese",
  ja: "Japanese",
  ko: "Korean",
  th: "Thai",
  vi: "Vietnamese",
  ar: "Arabic",
}

const COLORS: Record<string, string> = {
  tl: "hsl(var(--brand))",
  en: "hsl(var(--brand-accent))",
  ceb: "hsl(280 80% 60%)",
  ilo: "hsl(40 90% 55%)",
}

/** Friendly name for a language code; unknown codes fall back to the uppercased code. */
export function langLabel(code: string): string {
  if (!code) return "Unknown"
  return LABELS[code] ?? code.toUpperCase()
}

/** "Filipino (tl)" style label used by the breakdown widget. */
export function langLabelWithCode(code: string): string {
  if (!code) return "Unknown"
  return `${langLabel(code)} (${code})`
}

/** Stable, distinct color for a language code. Known codes use brand colors;
 *  unknown codes derive a deterministic hue from the string. */
export function langColor(code: string): string {
  if (COLORS[code]) return COLORS[code]
  let hash = 0
  for (let i = 0; i < code.length; i++) hash = (hash * 31 + code.charCodeAt(i)) | 0
  const hue = Math.abs(hash) % 360
  return `hsl(${hue} 65% 55%)`
}
