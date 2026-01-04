import { NextResponse } from "next/server";
import type { AuthRow, InsightsResponse, ReportFilters, SettlementRow } from "@/lib/types";
import { MOCK_REPORTS, getReportById } from "@/lib/mockReports";
import {
  computeAuthKpis,
  computeSettlementKpis,
  declinesByHour,
  filterReportRows,
  formatInt,
  formatMoneyUSD,
  formatPercent,
  networkComparisonFromReports,
  transactionsOverTimeFromAuth,
  transactionsOverTimeFromSettlement,
} from "@/lib/analytics";

// AI-ready (mock): deterministic insight generation over known mock data.
// In a future RAG pipeline, this would call an LLM with grounded metrics + citations.

type Req = {
  reportId: string;
  filters: ReportFilters;
};

function sum(arr: number[]) {
  return arr.reduce((a, b) => a + b, 0);
}

export async function POST(req: Request) {
  const body = (await req.json()) as Req;
  const filters = body.filters;

  const selected = getReportById(body.reportId) ?? MOCK_REPORTS[0]!;

  // Pull auth + settlement data relevant to filter/network.
  const authReports = MOCK_REPORTS.filter((r) => r.type === "Authorization").filter((r) =>
    filters.network === "All" ? true : r.network === filters.network,
  );
  const settleReports = MOCK_REPORTS.filter((r) => r.type === "Settlement").filter((r) =>
    filters.network === "All" ? true : r.network === filters.network,
  );

  const authRows = authReports.flatMap((r) => filterReportRows(r, { ...filters, network: "All" }) as AuthRow[]);
  const stlRows = settleReports.flatMap((r) => filterReportRows(r, { ...filters, network: "All" }) as SettlementRow[]);

  const auth = computeAuthKpis(authRows);
  const stl = computeSettlementKpis(stlRows);

  // Transactions-over-time uses the selected report (keeps UI coherent).
  const selectedRows = filterReportRows(selected, filters);
  const transactionsOverTime =
    selected.type === "Authorization"
      ? transactionsOverTimeFromAuth(selectedRows as AuthRow[])
      : transactionsOverTimeFromSettlement(selectedRows as SettlementRow[]);

  // Declines by hour is always based on auth rows (even if viewing a settlement report).
  const declines = declinesByHour(authRows);

  // Compare Visa vs Mastercard without constraining to a single network filter.
  const comparison = networkComparisonFromReports(MOCK_REPORTS, {
    rangeDays: filters.rangeDays,
  });

  // Insight 1: late-night decline bump (10 PM onwards).
  const lateDeclines = sum(declines.filter((d) => d.hour >= 22).map((d) => d.declines));
  const dayDeclines = sum(declines.filter((d) => d.hour < 22).map((d) => d.declines));
  const latePerHour = lateDeclines / 2;
  const dayPerHour = dayDeclines / 22;
  const lateLift = dayPerHour === 0 ? 0 : (latePerHour - dayPerHour) / dayPerHour;

  // Insight 2: settlement delays vs cross-border.
  const cross = stlRows.filter((r) => r.crossBorder);
  const domestic = stlRows.filter((r) => !r.crossBorder);
  const avgCrossDelay = cross.length === 0 ? 0 : cross.reduce((s, r) => s + r.settlementDelayDays, 0) / cross.length;
  const avgDomDelay = domestic.length === 0 ? 0 : domestic.reduce((s, r) => s + r.settlementDelayDays, 0) / domestic.length;
  const delayDelta = avgCrossDelay - avgDomDelay;

  // Insight 3: interchange trend within the period (early vs late half).
  const sorted = [...stlRows].sort((a, b) => a.settlementDateISO.localeCompare(b.settlementDateISO));
  const mid = Math.floor(sorted.length / 2);
  const early = sorted.slice(0, mid);
  const late = sorted.slice(mid);
  const earlyFees = early.reduce((s, r) => s + r.interchangeFees, 0);
  const lateFees = late.reduce((s, r) => s + r.interchangeFees, 0);
  const feesLift = earlyFees === 0 ? 0 : (lateFees - earlyFees) / earlyFees;

  const response: InsightsResponse = {
    kpis: [
      {
        label: "Authorization success rate",
        value: formatPercent(auth.approvalRate),
        delta: lateLift > 0.03 ? `Late-night declines are elevated (+${(lateLift * 100).toFixed(0)}% per-hour vs daytime)` : undefined,
        tone: lateLift > 0.12 ? "warn" : "neutral",
      },
      {
        label: "Settlement volume (net)",
        value: formatMoneyUSD(stl.settlementVolume),
        delta: stl.avgDelay >= 1.2 ? `Avg settlement delay: ${stl.avgDelay.toFixed(1)} days` : undefined,
        tone: stl.avgDelay >= 1.6 ? "warn" : "neutral",
      },
      {
        label: "Interchange fees",
        value: formatMoneyUSD(stl.interchange),
        delta: feesLift > 0.02 ? `Trending upward within period (+${(feesLift * 100).toFixed(1)}%)` : undefined,
        tone: feesLift > 0.05 ? "warn" : "neutral",
      },
    ],
    charts: {
      transactionsOverTime,
      declinesByHour: declines,
      networkComparison: comparison,
    },
    insightCards: [
      {
        id: "ic_declines_10pm",
        title: `Authorization declines increased ${Math.max(0, Math.round(lateLift * 100))}% after 10 PM`,
        narrative:
          `Declines cluster in the late-night window (22:00–23:59 UTC). ` +
          `On a per-hour basis, late-night declines run ~${(lateLift * 100).toFixed(0)}% higher than daytime.`,
        supportingMetrics: [
          { label: "Approval rate", value: formatPercent(auth.approvalRate) },
          { label: "Late-night declines", value: formatInt(lateDeclines) },
          { label: "Total transactions", value: formatInt(auth.total) },
        ],
        severity: lateLift >= 0.18 ? "watch" : "info",
      },
      {
        id: "ic_settlement_delay_xborder",
        title: "Settlement delays correlate with cross-border transactions",
        narrative:
          `Cross-border batches show longer settlement delay than domestic. ` +
          `Average delay is ${avgCrossDelay.toFixed(1)}d (cross-border) vs ${avgDomDelay.toFixed(1)}d (domestic).`,
        supportingMetrics: [
          { label: "Cross-border share", value: formatPercent(stl.crossBorderShare) },
          { label: "Delay delta", value: `${delayDelta.toFixed(1)} days` },
          { label: "Net settlement", value: formatMoneyUSD(stl.settlementVolume) },
        ],
        severity: delayDelta >= 0.8 ? "watch" : "info",
      },
      {
        id: "ic_interchange_up",
        title: "Interchange fees trending upward month-over-month",
        narrative:
          `Within the current period, interchange fees increase in the latter half. ` +
          `This is consistent with higher cross-border mix and a modest upward fee-rate trend.`,
        supportingMetrics: [
          { label: "Interchange fees", value: formatMoneyUSD(stl.interchange) },
          { label: "Early vs late lift", value: formatPercent(feesLift) },
          { label: "Cross-border share", value: formatPercent(stl.crossBorderShare) },
        ],
        severity: feesLift >= 0.06 ? "watch" : "info",
      },
    ],
  };

  return NextResponse.json(response);
}


