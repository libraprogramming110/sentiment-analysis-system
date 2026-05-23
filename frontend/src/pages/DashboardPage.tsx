import { MessagesSquare, ThumbsUp, ThumbsDown, Star } from "lucide-react"
import { StatCard } from "@/components/widgets/StatCard"
import { SentimentDonut } from "@/components/widgets/SentimentDonut"
import { AspectBars } from "@/components/widgets/AspectBars"
import { TrendChart } from "@/components/widgets/TrendChart"
import { TopKeywords } from "@/components/widgets/TopKeywords"
import { TopIssues } from "@/components/widgets/TopIssues"
import { LanguageBreakdown } from "@/components/widgets/LanguageBreakdown"
import { api, useApi, EMPTY_SUMMARY } from "@/lib/api"

export function DashboardPage() {
  const { data: summary, loading } = useApi(api.summary, EMPTY_SUMMARY, [])
  const total = summary.total || 1
  const positivePct = Math.round((summary.positive / total) * 100)
  const negativePct = Math.round((summary.negative / total) * 100)

  return (
    <div className="space-y-6">
      {/* Stat row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Reviews"
          value={loading ? "—" : summary.total}
          icon={<MessagesSquare className="h-4 w-4" />}
          tone="brand"
          helper={`${summary.total} analyzed`}
        />
        <StatCard
          label="Positive"
          value={loading ? "—" : summary.positive}
          icon={<ThumbsUp className="h-4 w-4" />}
          tone="positive"
          helper={`${positivePct}% of all reviews`}
        />
        <StatCard
          label="Negative"
          value={loading ? "—" : summary.negative}
          icon={<ThumbsDown className="h-4 w-4" />}
          tone="negative"
          helper={`${negativePct}% — flag for follow-up`}
        />
        <StatCard
          label="Avg Rating"
          value={loading ? "—" : summary.avgRating}
          icon={<Star className="h-4 w-4" />}
          tone="neutral"
          helper="from review ratings"
        />
      </div>

      {/* Main grid */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <TrendChart />
          <AspectBars />
        </div>
        <div className="space-y-4">
          <SentimentDonut />
          <TopIssues />
          <LanguageBreakdown />
        </div>
      </div>

      {/* Bottom row */}
      <TopKeywords />
    </div>
  )
}
