"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { InsightsResponse, Kpi, InsightCard as InsightCardT } from "@/lib/types";
import { cn } from "@/lib/utils";

type ApiResp = InsightsResponse;

function KpiCard({ kpi }: { kpi: Kpi }) {
  const tone =
    kpi.tone === "good"
      ? "text-[var(--ps-good)]"
      : kpi.tone === "warn"
        ? "text-[var(--ps-warn)]"
        : kpi.tone === "bad"
          ? "text-[var(--ps-bad)]"
          : "text-white/70";
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="text-xs font-semibold text-white/60">{kpi.label}</div>
      <div className="mt-1 text-2xl font-semibold text-white">{kpi.value}</div>
      {kpi.delta ? (
        <div className={cn("mt-2 text-xs font-semibold", tone)}>{kpi.delta}</div>
      ) : null}
    </div>
  );
}

function InsightCard({ card }: { card: InsightCardT }) {
  const badgeTone = card.severity === "risk" ? "gold" : card.severity === "watch" ? "blue" : "neutral";
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-white">{card.title}</div>
        <Badge tone={badgeTone}>{card.severity.toUpperCase()}</Badge>
      </div>
      <div className="mt-2 text-sm leading-6 text-white/70">{card.narrative}</div>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {card.supportingMetrics.map((m) => (
          <div key={m.label} className="rounded-lg border border-white/10 bg-[var(--ps-panel)] px-3 py-2">
            <div className="text-[11px] font-semibold text-white/55">{m.label}</div>
            <div className="mt-0.5 text-xs font-semibold text-white">{m.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function InsightsPage() {
  const { selectedReportId, filters, selectedReport } = useDashboardStore();

  const [data, setData] = useState<ApiResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

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

  return (
    <div className="grid gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-semibold text-white">Insights</div>
          <div className="mt-1 text-xs text-white/60">
            Deterministic, analyst-style insights from mocked Visa/Mastercard reports. AI-ready APIs.
          </div>
        </div>
        <Badge tone="blue">/api/insights</Badge>
      </div>

      {emptyState ? (
        <Card>
          <CardContent className="py-10 text-sm text-white/70">{emptyState}</CardContent>
        </Card>
      ) : null}

      {data ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>KPIs</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {data.kpis.map((k) => (
                <KpiCard key={k.label} kpi={k} />
              ))}
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-12">
            <Card className="lg:col-span-7">
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Transactions over time</CardTitle>
                <div className="text-xs text-white/60">Count (filtered)</div>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.charts.transactionsOverTime}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="dateISO" stroke="rgba(255,255,255,0.55)" fontSize={12} />
                    <YAxis stroke="rgba(255,255,255,0.55)" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,26,46,0.98)",
                        border: "1px solid rgba(255,255,255,0.10)",
                        borderRadius: 10,
                        color: "rgba(255,255,255,0.9)",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke="var(--ps-gold)"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="lg:col-span-5">
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Declines by hour</CardTitle>
                <div className="text-xs text-white/60">Authorization only</div>
              </CardHeader>
              <CardContent className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.charts.declinesByHour}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                    <XAxis dataKey="hour" stroke="rgba(255,255,255,0.55)" fontSize={12} />
                    <YAxis stroke="rgba(255,255,255,0.55)" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,26,46,0.98)",
                        border: "1px solid rgba(255,255,255,0.10)",
                        borderRadius: 10,
                        color: "rgba(255,255,255,0.9)",
                      }}
                    />
                    <Bar dataKey="declines" fill="rgba(255,91,107,0.85)" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex items-center justify-between">
              <CardTitle>Visa vs Mastercard comparison</CardTitle>
              <div className="text-xs text-white/60">Cross-report view</div>
            </CardHeader>
            <CardContent className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.charts.networkComparison}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis dataKey="label" stroke="rgba(255,255,255,0.55)" fontSize={12} />
                  <YAxis stroke="rgba(255,255,255,0.55)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15,26,46,0.98)",
                      border: "1px solid rgba(255,255,255,0.10)",
                      borderRadius: 10,
                      color: "rgba(255,255,255,0.9)",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="visa" name="Visa" fill="rgba(247,182,0,0.9)" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="mastercard" name="Mastercard" fill="rgba(29,62,240,0.8)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex items-center justify-between">
              <CardTitle>AI Insight Cards</CardTitle>
              <Badge>Mock analyst</Badge>
            </CardHeader>
            <CardContent className="grid gap-3 lg:grid-cols-3">
              {data.insightCards.map((c) => (
                <InsightCard key={c.id} card={c} />
              ))}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}


