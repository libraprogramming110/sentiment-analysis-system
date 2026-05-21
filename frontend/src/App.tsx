import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { ReviewsPage } from "@/pages/ReviewsPage"
import { AnalyticsPage } from "@/pages/AnalyticsPage"
import { AnalyzePage } from "@/pages/AnalyzePage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/reviews" element={<ReviewsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/settings" element={<div className="text-sm text-muted-foreground">Settings — coming soon.</div>} />
          <Route path="/help" element={<div className="text-sm text-muted-foreground">Help — coming soon.</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
