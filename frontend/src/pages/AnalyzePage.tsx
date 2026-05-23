import { useState } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Sparkles, Loader2, Languages, Quote } from "lucide-react"
import { cn } from "@/lib/utils"
import { api, type AnalyzeResponse } from "@/lib/api"

const samples = [
  { lang: "Filipino", text: "Sobrang masarap ng adobo nila pero medyo mabagal ang serbisyo. Mura naman ang presyo." },
  { lang: "Cebuano",  text: "Lami kaayo ang lechon, pero hugaw ang banyo ug mahal ang prices." },
  { lang: "Ilocano",  text: "Naimas unay ti pinakbet ken nagsayaat ti serbisyo. Awan duduana, agsubliak." },
  { lang: "English",  text: "The food was amazing but the service was painfully slow. Worth it though." },
]

export function AnalyzePage() {
  const [input, setInput] = useState(samples[0].text)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function analyze() {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.analyze({ text: input })
      setResult(res)
    } catch (e) {
      setError(
        e instanceof Error
          ? "Analysis failed — is the backend running and the Groq key set? " + e.message
          : "Analysis failed."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand" />
            Live Analyze
          </CardTitle>
          <CardDescription>
            Paste any restaurant review — English, Filipino, Cebuano, Ilocano, or another language — to see the hybrid pipeline in action.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type or paste a review…"
            rows={6}
            className="w-full resize-none rounded-md border border-input bg-transparent p-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />

          <div className="flex flex-wrap gap-1.5">
            <span className="self-center text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Try:</span>
            {samples.map((s) => (
              <button
                key={s.lang}
                type="button"
                onClick={() => setInput(s.text)}
                className="rounded-md border bg-muted/50 px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {s.lang}
              </button>
            ))}
          </div>

          <Button onClick={analyze} disabled={loading || !input.trim()} className="w-full gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Analyzing with Llama 3.1…" : "Analyze with Hybrid Pipeline"}
          </Button>

          <p className="text-[11px] text-muted-foreground">
            Pipeline: NLTK clean → langdetect → Llama 3.1 8B (Groq) → rule-based aspect validate → TF-IDF keywords.
          </p>
        </CardContent>
      </Card>

      {/* Result */}
      <Card className={cn("transition-opacity", !result && !loading && "opacity-60")}>
        <CardHeader>
          <CardTitle className="text-base">Pipeline Output</CardTitle>
          <CardDescription>Structured ABSA result returned in a single LLM call</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!result && !loading && !error && (
            <div className="flex h-64 items-center justify-center text-center text-sm text-muted-foreground">
              Run the pipeline to see results.
            </div>
          )}

          {error && !loading && (
            <div className="flex h-64 items-center justify-center rounded-md border border-destructive/30 bg-destructive/5 p-4 text-center text-sm text-destructive">
              {error}
            </div>
          )}

          {loading && (
            <div className="space-y-3">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />
              ))}
            </div>
          )}

          {result && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Overall</p>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant={result.overall_sentiment === "positive" ? "positive" : result.overall_sentiment === "negative" ? "negative" : "neutral"}>
                      {result.overall_sentiment}
                    </Badge>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {(result.overall_confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                    <Languages className="h-3 w-3" /> Detected Language
                  </p>
                  <p className="mt-1.5 text-sm font-medium uppercase">{result.language}</p>
                </div>
              </div>

              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Aspect Sentiments</p>
                <div className="space-y-2">
                  {result.aspects.map((a) => (
                    <div key={a.aspect} className="rounded-md border bg-background p-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{a.aspect}</span>
                        <Badge variant={a.sentiment === "positive" ? "positive" : a.sentiment === "negative" ? "negative" : "neutral"}>
                          {a.sentiment}
                        </Badge>
                      </div>
                      <p className="mt-1.5 flex items-start gap-1.5 text-xs italic text-muted-foreground">
                        <Quote className="h-3 w-3 shrink-0 mt-0.5" />
                        {a.evidence}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Extracted Keywords</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.keywords.map((k) => (
                    <Badge key={k} variant="outline">{k}</Badge>
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
