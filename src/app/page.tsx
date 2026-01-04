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
                Visa-style reporting intelligence
              </div>
            </div>
          </div>
          <Badge tone="gold" className="hidden sm:inline-flex">
            Visa Hackathon (Mock)
          </Badge>
        </div>
        <div className="hidden items-center gap-4 md:flex">
          <nav className="flex items-center gap-1 text-sm font-semibold text-[color:var(--ps-muted)]">
            <a className="rounded-md px-3 py-2 hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]" href="/dashboard/insights">
              Dashboard
            </a>
            <a className="rounded-md px-3 py-2 hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]" href="/dashboard/reports">
              Reports
            </a>
            <a className="rounded-md px-3 py-2 hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]" href="/dashboard/chat">
              AI Chat
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Badge tone="blue">AI-ready</Badge>
            <Badge>Mocked data</Badge>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16 pt-10">
        <div className="grid gap-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border bg-[var(--ps-panel)] px-3 py-1 text-xs font-semibold text-[color:var(--ps-muted)] shadow-sm">
              Built for reporting intelligence · Not a payment system
            </div>

            <h1 className="mt-5 text-4xl font-semibold leading-[1.06] tracking-tight text-[color:var(--ps-fg)] md:text-6xl">
              PayScoper — Turn payment reports into{" "}
              <span className="text-[color:var(--ps-blue)]">intelligence</span>.
            </h1>

            <p className="mt-4 max-w-xl text-base leading-7 text-[color:var(--ps-muted)]">
              AI-powered analytics for Visa & Mastercard authorization, settlement, and reconciliation reports.
              Upload a file (mock), get dashboards instantly, then ask “why” in plain English.
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
                  Upload or select report packs
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Visa/Mastercard · Auth + settlement (mock parse)
                </div>
              </div>
              <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
                <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                  Dashboards
                </div>
                <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                  KPIs + charts in one click
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Trends, declines by hour, network comparisons
                </div>
              </div>
              <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
                <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                  Insights
                </div>
                <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                  Analyst answers that cite metrics
                </div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  Deterministic today · RAG-ready tomorrow
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
                    Dashboard snapshot
                  </div>
                  <div className="mt-0.5 text-xs text-[color:var(--ps-subtle)]">
                    What you get immediately after parsing a report
                  </div>
                </div>
                <Badge tone="blue">Live demo</Badge>
              </div>

              <div className="mt-5 overflow-hidden rounded-xl border">
                <div className="flex items-center justify-between bg-[var(--ps-panel-2)] px-4 py-3">
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Selected report
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                    <span className="rounded-full border bg-[var(--ps-panel)] px-2 py-1">
                      Last 7 days
                    </span>
                    <span className="rounded-full border bg-[var(--ps-panel)] px-2 py-1">
                      All networks
                    </span>
                  </div>
                </div>
                <div className="border-t bg-[var(--ps-panel)] p-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <KpiSmall label="Auth success rate" value="91.8%" note="Late-night declines" tone="warn" />
                    <KpiSmall label="Net settlement" value="$1.92M" note="Stable WoW" tone="neutral" />
                    <KpiSmall label="Interchange" value="$34.6K" note="Trending upward" tone="info" />
                  </div>

                  <div className="mt-4 rounded-xl border bg-[var(--ps-panel-2)] p-4">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                        Transactions over time
                      </div>
                      <div className="text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                        (sample)
                      </div>
                    </div>
                    <MiniSparkline />
                  </div>

                  <div className="mt-4 overflow-hidden rounded-xl border">
                    <div className="bg-[var(--ps-panel-2)] px-4 py-2 text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                      Exceptions (table preview)
                    </div>
                    <div className="divide-y bg-[var(--ps-panel)]">
                      <MiniRow k="22:40 UTC" m="Issuer unavailable (91)" v="12 declines" />
                      <MiniRow k="23:10 UTC" m="Do not honor (05)" v="9 declines" />
                      <MiniRow k="02:05 UTC" m="Switch inoperative (91)" v="7 declines" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 overflow-hidden rounded-xl border">
                <div className="flex items-center justify-between bg-[var(--ps-panel-2)] px-4 py-3">
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    AI insight card (mock)
                  </div>
                  <div className="text-xs font-semibold text-[color:var(--ps-blue)]">
                    Deterministic
                  </div>
                </div>
                <div className="space-y-0 border-t bg-[var(--ps-panel)]">
                  <div className="px-4 py-3">
                    <div className="text-sm font-semibold text-[color:var(--ps-fg)]">
                      Declines increased after 10 PM
                    </div>
                    <div className="mt-1 text-xs leading-5 text-[color:var(--ps-muted)]">
                      Late-night declines run higher than daytime on a per-hour basis. Next cut: isolate issuer response codes
                      and merchant entry mode to confirm the driver.
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge tone="gold">Watch</Badge>
                      <Badge>Issuer codes</Badge>
                      <Badge>Entry mode</Badge>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-5 border-t pt-4 text-xs text-[color:var(--ps-subtle)]">
                AI is mocked and deterministic. API routes are structured for future RAG integration.
              </div>
            </div>
          </div>
        </div>

        <section className="mt-16">
          <div className="rounded-2xl border bg-[var(--ps-panel-2)] p-8">
            <div className="grid gap-6 md:grid-cols-12 md:items-start">
              <div className="md:col-span-5">
                <div className="text-sm font-semibold text-[color:var(--ps-fg)]">
                  How PayScope works
                </div>
                <div className="mt-2 text-sm leading-6 text-[color:var(--ps-muted)]">
                  A lightweight intelligence layer on top of existing Visa/Mastercard reports—built for fast investigation and clean executive summaries.
                </div>
              </div>
              <div className="md:col-span-7">
                <div className="grid gap-3 sm:grid-cols-3">
                  <Step n="01" title="Ingest" desc="Upload CSV/Excel/PDF (mock), parse into a normalized model." />
                  <Step n="02" title="Visualize" desc="KPIs + charts generated from report metrics in seconds." />
                  <Step n="03" title="Explain" desc="Ask “what changed and why?”—answers reference numbers." />
                </div>
              </div>
            </div>
          </div>
        </section>
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

function Step({ n, title, desc }: { n: string; title: string; desc: string }) {
  return (
    <div className="rounded-xl border bg-[var(--ps-panel)] p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">{title}</div>
        <div className="text-xs font-semibold text-[color:var(--ps-blue)]">{n}</div>
      </div>
      <div className="mt-2 text-sm font-semibold text-[color:var(--ps-fg)]">{desc}</div>
    </div>
  );
}

function KpiSmall({
  label,
  value,
  note,
  tone,
}: {
  label: string;
  value: string;
  note: string;
  tone: "warn" | "neutral" | "info";
}) {
  const noteClass =
    tone === "warn"
      ? "text-[color:var(--ps-warn)]"
      : tone === "info"
        ? "text-[color:var(--ps-blue)]"
        : "text-[color:var(--ps-subtle)]";
  return (
    <div className="rounded-xl border bg-[var(--ps-panel-2)] p-4">
      <div className="text-[11px] font-semibold text-[color:var(--ps-subtle)]">{label}</div>
      <div className="mt-1 text-lg font-semibold text-[color:var(--ps-fg)]">{value}</div>
      <div className={`mt-1 text-[11px] font-semibold ${noteClass}`}>{note}</div>
    </div>
  );
}

function MiniRow({ k, m, v }: { k: string; m: string; v: string }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2">
      <div className="text-[11px] font-semibold text-[color:var(--ps-subtle)]">{k}</div>
      <div className="min-w-0 flex-1 truncate text-[11px] text-[color:var(--ps-muted)]">{m}</div>
      <div className="text-[11px] font-semibold text-[color:var(--ps-fg)]">{v}</div>
    </div>
  );
}

function MiniSparkline() {
  // Simple, static SVG sparkline (no client JS, no charts dependency on landing).
  return (
    <div className="mt-3">
      <svg viewBox="0 0 240 60" className="h-[54px] w-full">
        <path
          d="M0 42 C 20 40, 28 30, 40 34 C 55 40, 66 46, 80 32 C 92 20, 110 16, 122 22 C 138 30, 150 28, 164 18 C 180 6, 202 14, 220 20 C 228 22, 234 20, 240 16"
          fill="none"
          stroke="rgba(20,52,203,0.85)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <path
          d="M0 60 L0 42 C 20 40, 28 30, 40 34 C 55 40, 66 46, 80 32 C 92 20, 110 16, 122 22 C 138 30, 150 28, 164 18 C 180 6, 202 14, 220 20 C 228 22, 234 20, 240 16 L240 60 Z"
          fill="rgba(20,52,203,0.10)"
        />
        <line x1="0" y1="59.5" x2="240" y2="59.5" stroke="rgba(15,23,42,0.12)" />
      </svg>
      <div className="mt-1 flex items-center justify-between text-[11px] text-[color:var(--ps-subtle)]">
        <span>Dec 18</span>
        <span>Dec 24</span>
      </div>
    </div>
  );
}
