import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  MessagesSquare,
  BarChart3,
  Sparkles,
  Settings,
  HelpCircle,
} from "lucide-react"
import { Logo } from "@/components/brand/Logo"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"

const nav = [
  { to: "/",          label: "Dashboard", icon: LayoutDashboard },
  { to: "/reviews",   label: "Reviews",   icon: MessagesSquare },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/analyze",   label: "Live Analyze", icon: Sparkles },
]

const footerNav = [
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/help",     label: "Help",     icon: HelpCircle },
]

export function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-60 shrink-0 border-r bg-card/60 backdrop-blur-sm">
      <div className="px-5 py-5">
        <Logo />
      </div>

      <Separator />

      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Workspace
        </p>
        {nav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-3 space-y-1">
        {footerNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="m-3 mt-0 rounded-lg border bg-muted/40 p-3">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-brand to-brand-accent" />
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-foreground">Casa Adobo</p>
            <p className="truncate text-[10px] text-muted-foreground">Single restaurant</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
