import { Badge } from "@/components/ui/Badge";
import { LinkButton } from "@/components/ui/Button";

export default function Home() {
  return (
    <div className="min-h-screen bg-[var(--ps-bg)]">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-lg border bg-[var(--ps-panel)] shadow-sm">
              <div className="h-2.5 w-2.5 rounded-full bg-[var(--ps-blue)]" />
            </div>
            <div>
              <div className="text-base font-semibold tracking-tight text-[color:var(--ps-fg)]">
                PayScope
              </div>
              <div className="text-xs text-[color:var(--ps-subtle)]">
                Visa-style internal analytics demo
              </div>
            </div>
          </div>
          <Badge tone="gold" className="hidden sm:inline-flex">
            Visa Hackathon (Mock)
          </Badge>
        </div>
        <div className="hidden items-center gap-2 md:flex">
          <Badge tone="blue">AI-ready</Badge>
          <Badge>Mocked data</Badge>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border bg-[var(--ps-panel)] px-3 py-1 text-xs font-semibold text-[color:var(--ps-muted)] shadow-sm">
              Built for reporting intelligence · Not a payment system
            </div>

            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight text-[color:var(--ps-fg)] md:text-6xl">
              PayScoper — Turn Payment Reports into Intelligence
            </h1>

            <p className="mt-4 max-w-xl text-base leading-7 text-[color:var(--ps-muted)]">
              AI-powered analytics for Visa & Mastercard authorization, settlement, and reconciliation reports.
              Transform static files into interactive dashboards and analyst-style explanations.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <LinkButton href="/dashboard" variant="primary">
                View Demo Dashboard
              </LinkButton>
              <LinkButton
                href="/dashboard/reports?sample=1"
                variant="secondary"
              >
                Upload Sample Report
              </LinkButton>
            </div>

            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
                <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                  Reports
                </div>
                <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                  Upload or select Visa/Mastercard files
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Authorization + settlement formats (mock parse)
                </div>
              </div>
              <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
                <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                  Dashboards
                </div>
                <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                  KPIs + charts, instantly generated
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Declines by hour, trends, comparisons
                </div>
              </div>
              <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
                <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                  Insights
                </div>
                <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                  Analyst-style explanations you can ask for
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Deterministic mock AI, AI-ready structure
                </div>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-3 text-xs text-[color:var(--ps-subtle)]">
              <span className="inline-flex items-center gap-2 rounded-full border bg-[var(--ps-panel)] px-3 py-1 shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--ps-blue)]" />
                Enterprise-grade UX
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border bg-[var(--ps-panel)] px-3 py-1 shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--ps-gold)]" />
                Deterministic demo data
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border bg-[var(--ps-panel)] px-3 py-1 shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--ps-good)]" />
                AI-ready API routes
              </span>
            </div>
          </div>

          <div className="md:col-span-5">
            <div className="rounded-2xl border bg-[var(--ps-panel)] p-6 shadow-[var(--ps-shadow)]">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-[color:var(--ps-fg)]">
                    Intelligence Brief
                  </div>
                  <div className="mt-0.5 text-xs text-[color:var(--ps-subtle)]">
                    Example output from a parsed authorization report
                  </div>
                </div>
                <Badge tone="blue">Demo</Badge>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border bg-[var(--ps-panel-2)] p-4">
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Authorization success rate
                  </div>
                  <div className="mt-1 text-2xl font-semibold text-[color:var(--ps-fg)]">
                    91.8%
                  </div>
                  <div className="mt-2 text-xs font-semibold text-[color:var(--ps-warn)]">
                    Declines elevated after 10 PM
                  </div>
                </div>
                <div className="rounded-xl border bg-[var(--ps-panel-2)] p-4">
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Net settlement volume
                  </div>
                  <div className="mt-1 text-2xl font-semibold text-[color:var(--ps-fg)]">
                    $1.92M
                  </div>
                  <div className="mt-2 text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Interchange trending upward
                  </div>
                </div>
              </div>

              <div className="mt-4 overflow-hidden rounded-xl border">
                <div className="flex items-center justify-between bg-[var(--ps-panel-2)] px-4 py-3">
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Key observations
                  </div>
                  <div className="text-xs font-semibold text-[color:var(--ps-blue)]">
                    Generated
                  </div>
                </div>
                <div className="space-y-0 border-t bg-[var(--ps-panel)]">
                  <Row label="Declines by hour" value="Peak 22:00–23:00 UTC" />
                  <Row label="Cross-border correlation" value="Higher settlement delays" />
                  <Row label="Network comparison" value="Visa vs Mastercard deltas" />
                </div>
              </div>

              <div className="mt-5 border-t pt-4 text-xs text-[color:var(--ps-subtle)]">
                AI is mocked and deterministic. API routes are structured for future RAG integration.
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3">
      <div className="text-sm font-semibold text-[color:var(--ps-fg)]">{label}</div>
      <div className="text-xs font-semibold text-[color:var(--ps-muted)]">{value}</div>
    </div>
  );
}
