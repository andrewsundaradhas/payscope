import { Badge } from "@/components/ui/Badge";
import { LinkButton } from "@/components/ui/Button";

export default function Home() {
  return (
    <div className="min-h-screen bg-[var(--ps-bg)]">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="text-base font-semibold tracking-tight text-white">
            PayScope
          </div>
          <Badge tone="gold">Visa Hackathon (Mock)</Badge>
        </div>
        <div className="hidden items-center gap-2 md:flex">
          <Badge tone="blue">AI-ready</Badge>
          <Badge>Mocked data</Badge>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16 pt-12">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-white/80">
              Built for reporting intelligence (not a payment system)
            </div>

            <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight text-white md:text-5xl">
              PayScoper — Turn Payment Reports into Intelligence
            </h1>

            <p className="mt-4 max-w-xl text-base leading-7 text-white/70">
              AI-powered analytics for Visa & Mastercard authorization,
              settlement, and reconciliation reports.
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

            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-[var(--ps-panel)] p-4">
                <div className="text-xs font-semibold text-white/60">
                  Upload or select reports
                </div>
                <div className="mt-1 text-sm font-semibold text-white">
                  Authorization + settlement
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-[var(--ps-panel)] p-4">
                <div className="text-xs font-semibold text-white/60">
                  Dynamic dashboards
                </div>
                <div className="mt-1 text-sm font-semibold text-white">
                  KPIs + charts
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-[var(--ps-panel)] p-4">
                <div className="text-xs font-semibold text-white/60">
                  Conversational insights
                </div>
                <div className="mt-1 text-sm font-semibold text-white">
                  Analyst-style answers
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-5">
            <div className="rounded-2xl border border-white/10 bg-[var(--ps-panel)] p-6 shadow-[var(--ps-shadow)]">
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-white">
                  Demo Highlights
                </div>
                <Badge tone="blue">Mock AI</Badge>
              </div>

              <div className="mt-5 space-y-3 text-sm text-white/75">
                <div className="flex items-start justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                  <div>
                    <div className="font-semibold text-white">Declines by hour</div>
                    <div className="text-xs text-white/60">
                      Spot spikes after 10 PM
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-[var(--ps-gold)]">
                    Watch
                  </div>
                </div>
                <div className="flex items-start justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                  <div>
                    <div className="font-semibold text-white">
                      Settlement delays
                    </div>
                    <div className="text-xs text-white/60">
                      Correlate cross-border batches
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-[var(--ps-gold)]">
                    Insight
                  </div>
                </div>
                <div className="flex items-start justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                  <div>
                    <div className="font-semibold text-white">
                      Visa vs Mastercard
                    </div>
                    <div className="text-xs text-white/60">
                      Compare approval & volume
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-[var(--ps-gold)]">
                    Compare
                  </div>
                </div>
              </div>

              <div className="mt-6 border-t border-white/10 pt-5 text-xs text-white/60">
                AI is mocked and deterministic. API routes are structured for
                future RAG integration.
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
