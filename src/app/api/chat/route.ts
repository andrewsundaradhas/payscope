import { NextResponse } from "next/server";
import type { AuthRow, ChatRequest, ChatResponse, SettlementRow } from "@/lib/types";
import { MOCK_REPORTS, getReportById } from "@/lib/mockReports";
import {
  computeAuthKpis,
  computeSettlementKpis,
  declinesByHour,
  filterReportRows,
  formatInt,
  formatMoneyUSD,
  formatPercent,
  lastNDaysRangeEndInclusive,
} from "@/lib/analytics";

// AI-ready (mock): deterministic analyst-style responses over structured metrics.
// Future: swap the rule-based router with an LLM, grounded by computed metrics + retrieved rows.

function lower(s: string) {
  return s.toLowerCase();
}

function sum(nums: number[]) {
  return nums.reduce((a, b) => a + b, 0);
}

export async function POST(req: Request) {
  const body = (await req.json()) as ChatRequest;
  const selected = getReportById(body.reportId) ?? MOCK_REPORTS[0]!;
  const filters = body.filters;
  const q = lower(body.question ?? "");

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

  const metricsBase = [
    { label: "Authorization approval rate", value: formatPercent(auth.approvalRate) },
    { label: "Authorization transactions", value: formatInt(auth.total) },
    { label: "Net settlement volume", value: formatMoneyUSD(stl.settlementVolume) },
    { label: "Interchange fees", value: formatMoneyUSD(stl.interchange) },
  ];

  // 1) Settlement drop analysis
  if (q.includes("settlement") && (q.includes("drop") || q.includes("decrease"))) {
    // Compare last 7 days vs previous 7 days within the available settlement range.
    const sorted = [...stlRows].sort((a, b) => a.settlementDateISO.localeCompare(b.settlementDateISO));
    const endISO = selected.type === "Settlement" ? selected.dateRange.endISO : (sorted[sorted.length - 1]?.settlementDateISO ?? selected.dateRange.endISO);
    const last7 = lastNDaysRangeEndInclusive(7, endISO);
    const prev7 = { startMs: last7.startMs - 7 * 24 * 60 * 60 * 1000, endMs: last7.startMs - 1 };

    const inRange = (r: SettlementRow, range: { startMs: number; endMs: number }) => {
      const t = new Date(r.settlementDateISO).getTime();
      return t >= range.startMs && t <= range.endMs;
    };

    const last = sorted.filter((r) => inRange(r, last7));
    const prev = sorted.filter((r) => inRange(r, prev7));
    const lastNet = last.reduce((s, r) => s + r.netAmount, 0);
    const prevNet = prev.reduce((s, r) => s + r.netAmount, 0);
    const delta = prevNet === 0 ? 0 : (lastNet - prevNet) / prevNet;

    const lastCross = last.filter((r) => r.crossBorder).length;
    const prevCross = prev.filter((r) => r.crossBorder).length;
    const lastAvgDelay = last.length === 0 ? 0 : last.reduce((s, r) => s + r.settlementDelayDays, 0) / last.length;
    const prevAvgDelay = prev.length === 0 ? 0 : prev.reduce((s, r) => s + r.settlementDelayDays, 0) / prev.length;

    const answer =
      `Looking at the settlement batches in the selected date window, net settlement volume changed ` +
      `${delta >= 0 ? "up" : "down"} by ${(Math.abs(delta) * 100).toFixed(1)}% in the last 7 days vs the prior 7 days.\n\n` +
      `Two drivers to check:\n` +
      `1) Cross-border mix: ${lastCross}/${last.length} batches cross-border last week vs ${prevCross}/${prev.length} prior week.\n` +
      `2) Timing: avg settlement delay moved from ${prevAvgDelay.toFixed(1)}d to ${lastAvgDelay.toFixed(1)}d, which can shift recognized volume across weeks.\n\n` +
      `If you want, I can break this down by merchant to pinpoint which settlement batches contributed most to the change.`;

    const resp: ChatResponse = {
      answer,
      metricsUsed: [
        { label: "Last 7d net settlement", value: formatMoneyUSD(lastNet) },
        { label: "Prior 7d net settlement", value: formatMoneyUSD(prevNet) },
        { label: "Net delta", value: `${(delta * 100).toFixed(1)}%` },
      ],
      followups: [
        "Break down the settlement drop by merchant",
        "Show cross-border vs domestic settlement volume trends",
        "Did interchange fees rise in the same window?",
      ],
    };
    return NextResponse.json(resp);
  }

  // 2) Network approval rate comparison
  if (q.includes("compare") && q.includes("visa") && (q.includes("master") || q.includes("mastercard")) && q.includes("approval")) {
    const visaAuth = MOCK_REPORTS.find((r) => r.type === "Authorization" && r.network === "Visa");
    const mcAuth = MOCK_REPORTS.find((r) => r.type === "Authorization" && r.network === "Mastercard");

    const vRows = visaAuth ? (filterReportRows(visaAuth, { ...filters, network: "All" }) as AuthRow[]) : [];
    const mRows = mcAuth ? (filterReportRows(mcAuth, { ...filters, network: "All" }) as AuthRow[]) : [];
    const vk = computeAuthKpis(vRows);
    const mk = computeAuthKpis(mRows);

    const gap = (vk.approvalRate - mk.approvalRate) * 100;
    const answer =
      `In the selected date window, Visa approval rate is ${formatPercent(vk.approvalRate)} vs Mastercard at ${formatPercent(mk.approvalRate)} ` +
      `(${gap >= 0 ? "+" : ""}${gap.toFixed(1)} pp Visa minus Mastercard).\n\n` +
      `If you want a “why”, the fastest next cut is declines by hour and top decline reasons per network (e.g., issuer unavailability vs insufficient funds).`;

    const resp: ChatResponse = {
      answer,
      metricsUsed: [
        { label: "Visa approval rate", value: formatPercent(vk.approvalRate) },
        { label: "Mastercard approval rate", value: formatPercent(mk.approvalRate) },
        { label: "Gap", value: `${gap >= 0 ? "+" : ""}${gap.toFixed(1)} pp` },
      ],
      followups: [
        "Show declines by hour for Visa vs Mastercard",
        "What are the top decline reasons by network?",
        "Which merchants drive the approval-rate gap?",
      ],
    };
    return NextResponse.json(resp);
  }

  // 3) Chargeback merchants
  if (q.includes("chargeback")) {
    const byMerchant = new Map<string, { name: string; chargebacks: number; tx: number }>();
    for (const r of authRows) {
      const k = r.merchantId;
      const cur = byMerchant.get(k) ?? { name: r.merchantName, chargebacks: 0, tx: 0 };
      cur.tx += 1;
      if (r.chargebackFlag) cur.chargebacks += 1;
      byMerchant.set(k, cur);
    }

    const ranked = Array.from(byMerchant.values())
      .sort((a, b) => b.chargebacks - a.chargebacks || b.tx - a.tx)
      .slice(0, 5);

    const answer =
      `In the selected authorization data, chargebacks are rare (this is a mock dataset), but the highest counts are concentrated in a few merchants:\n\n` +
      ranked
        .map((m, i) => `${i + 1}) ${m.name}: ${m.chargebacks} chargebacks across ${m.tx} authorizations`)
        .join("\n") +
      `\n\nIf you want to prioritize investigation, the next step is to normalize by volume (chargeback rate) and segment by entry mode (ecommerce vs card-present).`;

    const resp: ChatResponse = {
      answer,
      metricsUsed: [
        { label: "Total chargebacks (flagged)", value: formatInt(auth.chargebacks) },
        { label: "Authorization transactions", value: formatInt(auth.total) },
      ],
      followups: [
        "Compute chargeback rate by merchant (per 10k tx)",
        "Segment chargebacks by entry mode",
        "Are chargebacks higher for cross-border merchants?",
      ],
    };
    return NextResponse.json(resp);
  }

  // Default: analyst summary grounded in key metrics + a late-night decline note.
  const declines = declinesByHour(authRows);
  const lateDeclines = sum(declines.filter((d) => d.hour >= 22).map((d) => d.declines));
  const totalDeclines = sum(declines.map((d) => d.declines));

  const resp: ChatResponse = {
    answer:
      `Here’s what stands out in the selected window:\n\n` +
      `- Authorization performance: approval rate is ${formatPercent(auth.approvalRate)} across ${formatInt(auth.total)} transactions.\n` +
      `- Declines: ${formatInt(totalDeclines)} total declines; ${formatInt(lateDeclines)} occur after 10 PM (UTC), indicating a late-night concentration.\n` +
      `- Settlement: net volume is ${formatMoneyUSD(stl.settlementVolume)} with interchange fees of ${formatMoneyUSD(stl.interchange)}.\n\n` +
      `Ask a specific “why” question (e.g., “what changed after 10 PM?” or “which merchants drove the settlement change?”) and I’ll break it down.`,
    metricsUsed: metricsBase,
    followups: [
      "Why did declines increase after 10 PM?",
      "Compare Visa vs Mastercard settlement volume",
      "Which decline reasons are most common?",
    ],
  };

  return NextResponse.json(resp);
}


