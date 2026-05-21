import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { languageBreakdown as fallback } from "@/lib/mockData"
import { api, useApi } from "@/lib/api"
import { Languages } from "lucide-react"

const langLabels: Record<string, string> = {
  en: "English (en)", tl: "Filipino (tl)", ceb: "Cebuano (ceb)", ilo: "Ilocano (ilo)",
}
const langColors: Record<string, string> = {
  tl: "hsl(var(--brand))",
  en: "hsl(var(--brand-accent))",
  ceb: "hsl(280 80% 60%)",
  ilo: "hsl(40 90% 55%)",
}

export function LanguageBreakdown() {
  const { data } = useApi(api.languages, { languages: [] }, [])

  // map backend rows {lang, count} → display rows; fallback keeps colors & nice labels
  const rows = data.languages.length
    ? data.languages.map((l) => ({
        lang:  langLabels[l.lang] ?? l.lang,
        count: l.count,
        color: langColors[l.lang] ?? "hsl(var(--muted-foreground))",
      }))
    : fallback

  const total = rows.reduce((s, l) => s + l.count, 0) || 1

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Languages className="h-4 w-4 text-brand" />
          Language Mix
        </CardTitle>
        <CardDescription>Multilingual NLP coverage</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex h-2 w-full overflow-hidden rounded-full bg-muted">
          {rows.map((l) => (
            <div key={l.lang} style={{ width: `${(l.count / total) * 100}%`, background: l.color }} />
          ))}
        </div>
        <div className="space-y-2">
          {rows.map((l) => (
            <div key={l.lang} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full" style={{ background: l.color }} />
                <span className="text-foreground">{l.lang}</span>
              </div>
              <span className="tabular-nums text-muted-foreground">
                {l.count} <span className="text-xs">({Math.round((l.count / total) * 100)}%)</span>
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
