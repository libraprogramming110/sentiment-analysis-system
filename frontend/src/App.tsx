import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { ReviewsPage } from "@/pages/ReviewsPage"
import { AnalyticsPage } from "@/pages/AnalyticsPage"
import { ComparePage } from "@/pages/ComparePage"
import { AnalyzePage } from "@/pages/AnalyzePage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/reviews" element={<ReviewsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
