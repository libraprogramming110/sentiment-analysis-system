import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Loader2 } from "lucide-react"
import { AuthProvider, useAuth } from "@/lib/auth"
import { LoginPage } from "@/pages/LoginPage"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { ReviewsPage } from "@/pages/ReviewsPage"
import { AnalyticsPage } from "@/pages/AnalyticsPage"
import { ComparePage } from "@/pages/ComparePage"
import { AnalyzePage } from "@/pages/AnalyzePage"

function Gate() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!user) return <LoginPage />

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

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  )
}
