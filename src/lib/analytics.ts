import type {
  AuthRow,
  CardNetwork,
  CardNetworkFilter,
  DateRangePreset,
  Report,
  ReportFilters,
  SettlementRow,
} from "@/lib/types";

export function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

export function formatMoneyUSD(amount: number) {
  const sign = amount < 0 ? "-" : "";
  const v = Math.abs(amount);
  return `${sign}$${v.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatPercent(p: number) {
  return `${(p * 100).toFixed(1)}%`;
}

export function formatInt(n: number) {
  return n.toLocaleString("en-US");
}

function parseISOToMs(iso: string) {
  return new Date(iso).getTime();
}

export function lastNDaysRangeEndInclusive(days: DateRangePreset, endISO: string) {
  const endMs = parseISOToMs(endISO);
  const startMs = endMs - (days - 1) * 24 * 60 * 60 * 1000;
  return { startMs, endMs };
}

function networkMatches(n: CardNetwork, filter: CardNetworkFilter) {
  return filter === "All" ? true : n === filter;
}

export function filterReportRows(report: Report, filters: ReportFilters) {
  const { startMs, endMs } = lastNDaysRangeEndInclusive(filters.rangeDays, report.dateRange.endISO);
  if (report.type === "Authorization") {
    const rows = report.rows as AuthRow[];
    return rows.filter((r) => {
      const t = parseISOToMs(r.timestampISO);
      return (
        t >= startMs &&
        t <= endMs &&
        networkMatches(r.network, filters.network)
      );
    });
  }
  const rows = report.rows as SettlementRow[];
  return rows.filter((r) => {
    const t = parseISOToMs(r.settlementDateISO);
    return (
      t >= startMs &&
      t <= endMs &&
      networkMatches(r.network, filters.network)
    );
  });
}

export function dayKeyUTC(iso: string) {
  // YYYY-MM-DD in UTC
  return iso.slice(0, 10);
}

export function transactionsOverTimeFromAuth(rows: AuthRow[]) {
  const byDay = new Map<string, number>();
  for (const r of rows) {
    const k = dayKeyUTC(r.timestampISO);
    byDay.set(k, (byDay.get(k) ?? 0) + 1);
  }
  return Array.from(byDay.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([dateISO, count]) => ({ dateISO, count }));
}

export function transactionsOverTimeFromSettlement(rows: SettlementRow[]) {
  const byDay = new Map<string, number>();
  for (const r of rows) {
    const k = dayKeyUTC(r.settlementDateISO);
    byDay.set(k, (byDay.get(k) ?? 0) + r.txCount);
  }
  return Array.from(byDay.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([dateISO, count]) => ({ dateISO, count }));
}

export function declinesByHour(rows: AuthRow[]) {
  const hours = Array.from({ length: 24 }, (_, h) => ({ hour: h, declines: 0 }));
  for (const r of rows) {
    if (r.approved) continue;
    const hour = new Date(r.timestampISO).getUTCHours();
    hours[clamp(hour, 0, 23)].declines += 1;
  }
  return hours;
}

export function computeAuthKpis(rows: AuthRow[]) {
  const total = rows.length;
  const approved = rows.filter((r) => r.approved).length;
  const declined = total - approved;
  const approvalRate = total === 0 ? 0 : approved / total;
  const declineRate = total === 0 ? 0 : declined / total;
  const authAmount = rows.reduce((sum, r) => sum + r.amount, 0);
  const chargebacks = rows.filter((r) => r.chargebackFlag).length;
  return {
    total,
    approved,
    declined,
    approvalRate,
    declineRate,
    authAmount,
    chargebacks,
  };
}

export function computeSettlementKpis(rows: SettlementRow[]) {
  const settlementVolume = rows.reduce((sum, r) => sum + r.netAmount, 0);
  const gross = rows.reduce((sum, r) => sum + r.grossAmount, 0);
  const interchange = rows.reduce((sum, r) => sum + r.interchangeFees, 0);
  const tx = rows.reduce((sum, r) => sum + r.txCount, 0);
  const crossBorderShare = rows.length === 0 ? 0 : rows.filter((r) => r.crossBorder).length / rows.length;
  const avgDelay =
    rows.length === 0
      ? 0
      : rows.reduce((sum, r) => sum + r.settlementDelayDays, 0) / rows.length;
  return { settlementVolume, gross, interchange, tx, crossBorderShare, avgDelay };
}

export function networkComparisonFromReports(
  reports: Report[],
  filters: Omit<ReportFilters, "network"> & { network?: never },
) {
  // Compare Visa vs Mastercard using best-fit authorization report if present; otherwise settlement.
  const authVisa = reports.find((r) => r.type === "Authorization" && r.network === "Visa");
  const authMc = reports.find((r) => r.type === "Authorization" && r.network === "Mastercard");
  const settleVisa = reports.find((r) => r.type === "Settlement" && r.network === "Visa");
  const settleMc = reports.find((r) => r.type === "Settlement" && r.network === "Mastercard");

  if (authVisa && authMc) {
    const v = filterReportRows(authVisa, { ...filters, network: "All" }) as AuthRow[];
    const m = filterReportRows(authMc, { ...filters, network: "All" }) as AuthRow[];
    const vk = computeAuthKpis(v);
    const mk = computeAuthKpis(m);
    return [
      { label: "Approval rate", visa: vk.approvalRate * 100, mastercard: mk.approvalRate * 100 },
      { label: "Decline rate", visa: vk.declineRate * 100, mastercard: mk.declineRate * 100 },
      { label: "Total auth $", visa: vk.authAmount, mastercard: mk.authAmount },
    ];
  }

  if (settleVisa && settleMc) {
    const v = filterReportRows(settleVisa, { ...filters, network: "All" }) as SettlementRow[];
    const m = filterReportRows(settleMc, { ...filters, network: "All" }) as SettlementRow[];
    const vk = computeSettlementKpis(v);
    const mk = computeSettlementKpis(m);
    return [
      { label: "Net settlement $", visa: vk.settlementVolume, mastercard: mk.settlementVolume },
      { label: "Interchange $", visa: vk.interchange, mastercard: mk.interchange },
      { label: "Transactions", visa: vk.tx, mastercard: mk.tx },
    ];
  }

  return [
    { label: "Approval rate", visa: 0, mastercard: 0 },
    { label: "Decline rate", visa: 0, mastercard: 0 },
    { label: "Transactions", visa: 0, mastercard: 0 },
  ];
}


