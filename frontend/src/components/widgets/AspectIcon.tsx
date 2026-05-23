import { Utensils, ConciergeBell, Armchair, Sparkles, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

// Shared aspect icons. Price keeps the ₱ currency symbol (it's informative, not an
// emoji); the rest render as lucide icons. Pass sizing via `className` — icons read
// h-/w-* utilities, the ₱ glyph reads text-* utilities, so include both when sizing.
const ICONS: Record<string, LucideIcon> = {
  food: Utensils,
  service: ConciergeBell,
  ambiance: Armchair,
  cleanliness: Sparkles,
}

export function AspectIcon({ aspect, className }: { aspect: string; className?: string }) {
  if (aspect === "price") {
    return (
      <span className={cn("inline-flex items-center justify-center font-semibold leading-none", className)}>
        ₱
      </span>
    )
  }
  const Icon = ICONS[aspect]
  return Icon ? <Icon className={className} /> : null
}
