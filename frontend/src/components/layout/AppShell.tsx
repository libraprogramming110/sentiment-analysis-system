import { Outlet, useLocation } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { Header } from "./Header"

const titles: Record<string, { title: string; subtitle: string }> = {
  "/":          { title: "Dashboard",      subtitle: "Overview of customer sentiment across all reviews." },
  "/reviews":   { title: "Reviews",        subtitle: "Browse, filter, and inspect every analyzed review." },
  "/analytics": { title: "Analytics",      subtitle: "Deep-dive into aspect performance and trends." },
  "/compare":   { title: "Compare",        subtitle: "Benchmark all restaurants side by side, grouped by city." },
  "/analyze":   { title: "Live Analyze",   subtitle: "Paste a review and get instant ABSA results." },
}

export function AppShell() {
  const { pathname } = useLocation()
  const meta = titles[pathname] ?? { title: "RestoPulse", subtitle: "" }

  return (
    <div className="flex h-svh w-full bg-background text-foreground">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1400px] p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
