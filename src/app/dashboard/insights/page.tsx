"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import { Badge } from "@/components/ui/Badge";
import type { InsightsResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

type ApiResp = InsightsResponse;

type View = "Overview" | "Declines" | "Settlement";
type HeroMetric = "Transactions" | "Declines";

export default function InsightsPage() {
  const { selectedReportId, filters, selectedReport } = useDashboardStore();

  const [data, setData] = useState<ApiResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [view, setView] = useState<View>("Overview");
  const [heroMetric, setHeroMetric] = useState<HeroMetric>("Transactions");

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setErr(null);
      try {
        const res = await fetch("/api/insights", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reportId: selectedReportId,
            filters,
          }),
        });
        if (!res.ok) throw new Error(`Insights failed (${res.status})`);
        const json = (await res.json()) as ApiResp;
        if (!cancelled) setData(json);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Insights error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (selectedReportId) void run();
    return () => {
      cancelled = true;
    };
  }, [selectedReportId, filters]);

  const emptyState = useMemo(() => {
    if (!selectedReport) return "Select a report to view insights.";
    if (loading) return "Generating insights…";
    if (err) return err;
    return null;
  }, [selectedReport, loading, err]);

  const header = useMemo(() => {
    const title = selectedReport ? `${selectedReport.type} insights` : "Insights";
    const subtitle = selectedReport
      ? `${selectedReport.network} · Last ${filters.rangeDays} days · ${filters.network === "All" ? "All networks" : filters.network}`
      : "Deterministic, analyst-style insights (mock)";
    return { title, subtitle };
  }, [selectedReport, filters]);

  const heroSeries = useMemo(() => {
    if (!data) return [];
    if (heroMetric === "Transactions") {
      return data.charts.transactionsOverTime.map((d) => ({
        x: d.dateISO,
        v: d.count,
      }));
    }
    // Declines metric uses hour buckets (render as a compact “curve”).
    return data.charts.declinesByHour.map((d) => ({
      x: `${d.hour}:00`,
      v: d.declines,
    }));
  }, [data, heroMetric]);

  const heroDelta = useMemo(() => {
    if (heroSeries.length < 2) return null;
    const a = heroSeries[heroSeries.length - 2]?.v ?? 0;
    const b = heroSeries[heroSeries.length - 1]?.v ?? 0;
    if (a === 0) return null;
    const pct = ((b - a) / a) * 100;
    return { pct, up: pct >= 0 };
  }, [heroSeries]);

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-semibold tracking-tight text-[color:var(--ps-fg)]">
            {header.title}
          </div>
          <div className="mt-1 text-sm text-[color:var(--ps-subtle)]">{header.subtitle}</div>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone="blue">/api/insights</Badge>
          <Badge>Mock</Badge>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {(["Overview", "Declines", "Settlement"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setView(t)}
            className={cn(
              "rounded-full border px-4 py-2 text-sm font-semibold transition",
              view === t
                ? "bg-[rgba(20,52,203,0.08)] text-[color:var(--ps-fg)]"
                : "bg-[var(--ps-panel)] text-[color:var(--ps-muted)] hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {emptyState ? (
        <div className="rounded-2xl border bg-[var(--ps-panel-2)] p-8 text-sm text-[color:var(--ps-muted)]">
          {emptyState}
        </div>
      ) : null}

      {data ? (
        <>
          <div className="grid gap-6 lg:grid-cols-12">
            {/* Left tiles */}
            <div className="lg:col-span-5">
              <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
                <KpiTile
                  title={data.kpis[0]?.label ?? "Authorization success rate"}
                  value={data.kpis[0]?.value ?? "—"}
                  note={data.kpis[0]?.delta ?? "Primary health signal"}
                  variant="green"
                />
                <KpiTile
                  title={data.kpis[1]?.label ?? "Settlement volume (net)"}
                  value={data.kpis[1]?.value ?? "—"}
                  note={data.kpis[1]?.delta ?? "Net settlement volume"}
                  variant="blue"
                />
                <KpiTile
                  title={data.kpis[2]?.label ?? "Interchange fees"}
                  value={data.kpis[2]?.value ?? "—"}
                  note={data.kpis[2]?.delta ?? "Cost trend"}
                  variant="ink"
                />
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                {["Nov 20", "Dec 20", "Jan 21", "Feb 21", "Mar 21", "Apr 21"].map((d, i) => (
                  <span
                    key={d}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs font-semibold",
                      i === 0
                        ? "bg-[color:var(--ps-ink)] text-white"
                        : "bg-[var(--ps-panel)] text-[color:var(--ps-subtle)]",
                    )}
                  >
                    {d}
                  </span>
                ))}
              </div>
            </div>

            {/* Right hero panel */}
            <div className="lg:col-span-7">
              <div className="overflow-hidden rounded-3xl border bg-[color:var(--ps-ink)] shadow-[var(--ps-shadow)]">
                <div className="flex flex-wrap items-start justify-between gap-4 px-6 pt-6">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-white/70">
                      {heroMetric === "Transactions"
                        ? "Transactions over time"
                        : "Declines by hour"}
                    </div>
                    <div className="mt-2 flex items-end gap-3">
                      <div className="text-5xl font-semibold leading-none tracking-tight text-white">
                        {heroSeries[heroSeries.length - 1]?.v ?? "—"}
                      </div>
                      {heroDelta ? (
                        <div
                          className={cn(
                            "mb-1 text-sm font-semibold",
                            heroDelta.up ? "text-[var(--ps-good)]" : "text-[var(--ps-bad)]",
                          )}
                        >
                          {heroDelta.up ? "+" : ""}
                          {heroDelta.pct.toFixed(0)}%
                        </div>
                      ) : null}
                    </div>
                    <div className="mt-1 text-sm text-white/70">
                      {heroMetric === "Transactions"
                        ? "Latest bucket count (selected report)"
                        : "Declines (authorization rows only)"}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setHeroMetric("Transactions")}
                      className={cn(
                        "rounded-full border border-white/10 px-3 py-1 text-xs font-semibold transition",
                        heroMetric === "Transactions"
                          ? "bg-white/10 text-white"
                          : "bg-transparent text-white/70 hover:bg-white/10 hover:text-white",
                      )}
                    >
                      Transactions
                    </button>
                    <button
                      type="button"
                      onClick={() => setHeroMetric("Declines")}
                      className={cn(
                        "rounded-full border border-white/10 px-3 py-1 text-xs font-semibold transition",
                        heroMetric === "Declines"
                          ? "bg-white/10 text-white"
                          : "bg-transparent text-white/70 hover:bg-white/10 hover:text-white",
                      )}
                    >
                      Declines
                    </button>
                  </div>
                </div>

                <div className="h-[260px] px-3 pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={heroSeries}>
                      <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                      <XAxis dataKey="x" stroke="rgba(255,255,255,0.55)" fontSize={12} />
                      <YAxis stroke="rgba(255,255,255,0.55)" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(11,18,32,0.98)",
                          border: "1px solid rgba(255,255,255,0.10)",
                          borderRadius: 12,
                          color: "rgba(255,255,255,0.92)",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="v"
                        stroke={heroMetric === "Transactions" ? "rgba(247,182,0,0.95)" : "rgba(255,91,107,0.95)"}
                        strokeWidth={3}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="grid gap-3 border-t border-white/10 px-6 py-5 sm:grid-cols-3">
                  <MiniHeroStat label={data.kpis[0]?.label ?? "Auth success rate"} value={data.kpis[0]?.value ?? "—"} />
                  <MiniHeroStat label={data.kpis[1]?.label ?? "Net settlement"} value={data.kpis[1]?.value ?? "—"} />
                  <MiniHeroStat label={data.kpis[2]?.label ?? "Interchange"} value={data.kpis[2]?.value ?? "—"} />
                </div>
              </div>
            </div>
          </div>

          {/* Lower “tables” section like the screenshot */}
          <div className="grid gap-6 lg:grid-cols-12">
            <div className="lg:col-span-6">
              <div className="text-xl font-semibold tracking-tight text-[color:var(--ps-fg)]">
                Analyst summary
              </div>
              <div className="mt-3 space-y-3">
                {data.insightCards.map((c) => (
                  <div key={c.id} className="rounded-2xl border bg-[var(--ps-panel)] p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-[color:var(--ps-fg)]">
                          {c.title}
                        </div>
                        <div className="mt-1 text-sm leading-6 text-[color:var(--ps-muted)]">
                          {c.narrative}
                        </div>
                      </div>
                      <Badge tone={c.severity === "risk" ? "gold" : c.severity === "watch" ? "blue" : "neutral"}>
                        {c.severity.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-3">
                      {c.supportingMetrics.map((m) => (
                        <div key={m.label} className="rounded-xl border bg-[var(--ps-panel-2)] px-4 py-3">
                          <div className="text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                            {m.label}
                          </div>
                          <div className="mt-1 text-sm font-semibold text-[color:var(--ps-fg)]">
                            {m.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-6">
              <div className="text-xl font-semibold tracking-tight text-[color:var(--ps-fg)]">
                Declines by hour
              </div>
              <div className="mt-3 rounded-2xl border bg-[var(--ps-panel)] p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold text-[color:var(--ps-fg)]">Distribution</div>
                  <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">
                    Authorization only
                  </div>
                </div>
                <div className="mt-3 h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.charts.declinesByHour}>
                      <CartesianGrid stroke="rgba(15,23,42,0.10)" vertical={false} />
                      <XAxis dataKey="hour" stroke="rgba(11,18,32,0.55)" fontSize={12} />
                      <YAxis stroke="rgba(11,18,32,0.55)" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(255,255,255,0.98)",
                          border: "1px solid rgba(15,23,42,0.12)",
                          borderRadius: 12,
                          color: "rgba(11,18,32,0.9)",
                        }}
                      />
                      <Bar dataKey="declines" fill="rgba(255,91,107,0.82)" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

function KpiTile({
  title,
  value,
  note,
  variant,
}: {
  title: string;
  value: string;
  note: string;
  variant: "green" | "blue" | "ink";
}) {
  const bg =
    variant === "green"
      ? "bg-[rgba(42,194,143,0.18)]"
      : variant === "blue"
        ? "bg-[rgba(20,52,203,0.12)]"
        : "bg-[color:var(--ps-ink)]";
  const fg = variant === "ink" ? "text-white" : "text-[color:var(--ps-fg)]";
  const sub = variant === "ink" ? "text-white/70" : "text-[color:var(--ps-subtle)]";
  const border = variant === "ink" ? "border-black/0" : "border";

  return (
    <div className={cn("rounded-3xl border p-5 shadow-sm", bg, border)}>
      <div className={cn("text-xs font-semibold", sub)}>{title}</div>
      <div className={cn("mt-3 text-3xl font-semibold tracking-tight", fg)}>{value}</div>
      <div className={cn("mt-2 text-xs font-semibold", sub)}>{note}</div>
    </div>
  );
}

function MiniHeroStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] font-semibold text-white/60">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

