import { cn } from "@/lib/utils"

interface LogoProps {
  className?: string
  showWordmark?: boolean
  size?: number
}

/**
 * RestoPulse mark — a circular pulse with a "fork tine" glyph.
 * Combines: restaurant (utensil) + analytics (pulse line).
 */
export function Logo({ className, showWordmark = true, size = 28 }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        {/* outer pulse ring */}
        <span
          className="absolute inset-0 rounded-full bg-brand/30 animate-pulse-ring"
          aria-hidden
        />
        <svg
          viewBox="0 0 32 32"
          width={size}
          height={size}
          className="relative"
          aria-hidden
        >
          <defs>
            <linearGradient id="rp-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="hsl(var(--brand))" />
              <stop offset="100%" stopColor="hsl(var(--brand-accent))" />
            </linearGradient>
          </defs>
          {/* mark background */}
          <rect width="32" height="32" rx="9" fill="url(#rp-grad)" />
          {/* pulse line */}
          <path
            d="M6 17 L11 17 L13 12 L16 22 L19 14 L21 17 L26 17"
            fill="none"
            stroke="white"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <span className="text-base font-semibold tracking-tight text-foreground">
            Resto<span className="text-brand">Pulse</span>
          </span>
          <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Review Intelligence
          </span>
        </div>
      )}
    </div>
  )
}
