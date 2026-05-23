import { useRef, useState } from "react"
import { Upload, Loader2, FileDown, CheckCircle2, AlertCircle } from "lucide-react"
import {
  Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api, type UploadResponse } from "@/lib/api"

const TEMPLATE_CSV = `review_text,rating,author,date,restaurant_name,city
"The adobo was amazing but the service was a bit slow.",4,Juan Dela Cruz,2026-05-01,Lola's Kitchen,Cagayan de Oro
"Sobrang init sa loob and ang mahal ng pagkain.",2,Maria Santos,2026-05-03,Lola's Kitchen,Cagayan de Oro
"Best lechon in town, super friendly staff!",5,Pedro Reyes,2026-05-10,Lola's Kitchen,Cagayan de Oro
`

function downloadTemplate() {
  const blob = new Blob([TEMPLATE_CSV], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "restopulse_reviews_template.csv"
  a.click()
  URL.revokeObjectURL(url)
}

export function UploadDialog({ onUploaded }: { onUploaded: () => void }) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [datasetName, setDatasetName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  function reset() {
    setFile(null); setDatasetName(""); setError(null); setResult(null); setLoading(false)
    if (fileRef.current) fileRef.current.value = ""
  }

  async function submit() {
    if (!file) return
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await api.upload(file, datasetName || undefined)
      setResult(res)
      onUploaded()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => { setOpen(o); if (!o) reset() }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2 whitespace-nowrap">
          <Upload className="h-4 w-4" /> Upload CSV
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-4 w-4 text-brand" /> Upload reviews (CSV)
          </DialogTitle>
          <DialogDescription>
            Add reviews on top of the existing dataset. Each review is analyzed by the hybrid
            pipeline, so this takes a few seconds per row.
          </DialogDescription>
        </DialogHeader>

        {!result ? (
          <div className="space-y-4">
            <div className="rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
              <p>
                Required column: <code className="font-medium text-foreground">review_text</code>.
                Optional: <code>rating</code>, <code>author</code>, <code>date</code>,{" "}
                <code>restaurant_name</code>, <code>city</code>. Max <span className="font-medium text-foreground">30</span> rows.
              </p>
              <button
                type="button"
                onClick={downloadTemplate}
                className="mt-2 inline-flex items-center gap-1.5 font-medium text-brand hover:underline"
              >
                <FileDown className="h-3.5 w-3.5" /> Download template
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium">CSV file</label>
              <Input
                ref={fileRef}
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(null) }}
                className="cursor-pointer file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-muted file:px-2 file:py-1 file:text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium">
                Dataset name <span className="text-muted-foreground">(optional — used when a row has no restaurant_name)</span>
              </label>
              <Input
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="e.g. My Restaurant"
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button onClick={submit} disabled={!file || loading} className="w-full gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {loading ? "Analyzing reviews…" : "Upload & analyze"}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-start gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
              <div>
                <p className="font-medium text-foreground">Upload complete</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Added <span className="font-medium text-foreground">{result.inserted}</span> reviews
                  {result.restaurants_created > 0 && <> across <span className="font-medium text-foreground">{result.restaurants_created}</span> restaurant(s)</>}.
                  Dataset now has <span className="font-medium text-foreground">{result.new_total}</span> reviews.
                  {result.skipped > 0 && <> ({result.skipped} skipped)</>}
                  {result.failed > 0 && <> ({result.failed} failed)</>}
                </p>
              </div>
            </div>
            {result.errors.length > 0 && (
              <ul className="space-y-1 rounded-md border bg-muted/40 p-3 text-xs text-muted-foreground">
                {result.errors.map((e, i) => <li key={i}>• {e}</li>)}
              </ul>
            )}
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={reset}>Upload another</Button>
              <Button className="flex-1" onClick={() => { setOpen(false); reset() }}>Done</Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
