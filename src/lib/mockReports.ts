import type {
  AuthRow,
  CardNetwork,
  Report,
  ReportSummary,
  ReportType,
  SettlementRow,
} from "@/lib/types";

type Seed = string;

function stableHash(seed: Seed) {
  // Small deterministic hash (not crypto), stable across runtimes.
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

function pick<T>(arr: readonly T[], n: number) {
  return arr[n % arr.length];
}

function pad2(n: number) {
  return n.toString().padStart(2, "0");
}

function isoUTC(y: number, m: number, d: number, hh = 0, mm = 0, ss = 0) {
  return `${y}-${pad2(m)}-${pad2(d)}T${pad2(hh)}:${pad2(mm)}:${pad2(ss)}Z`;
}

const MERCHANTS = [
  { id: "m_athena", name: "Athena Grocers", country: "US", mcc: "5411" },
  { id: "m_orbit", name: "Orbit Electronics", country: "US", mcc: "5732" },
  { id: "m_summit", name: "Summit Travel", country: "GB", mcc: "4722" },
  { id: "m_bistro", name: "Bistro North", country: "CA", mcc: "5812" },
  { id: "m_pixel", name: "Pixel Subscriptions", country: "US", mcc: "4816" },
  { id: "m_lumen", name: "Lumen Apparel", country: "DE", mcc: "5651" },
] as const;

const DECLINES = [
  { code: "05", reason: "Do not honor" },
  { code: "51", reason: "Insufficient funds" },
  { code: "54", reason: "Expired card" },
  { code: "57", reason: "Transaction not permitted" },
  { code: "91", reason: "Issuer or switch inoperative" },
] as const;

const ENTRY_MODES: AuthRow["entryMode"][] = [
  "Chip",
  "Contactless",
  "Ecommerce",
  "Magstripe",
];

function makeAuthRows(seed: Seed, network: CardNetwork, y = 2025, m = 12) {
  const base = stableHash(seed + network);
  const rows: AuthRow[] = [];
  // 7 days, 24 hours, ~2 tx/hr with increased declines after 22:00
  for (let day = 18; day <= 24; day++) {
    for (let hour = 0; hour < 24; hour++) {
      const txPerHour = hour % 3 === 0 ? 3 : 2;
      for (let j = 0; j < txPerHour; j++) {
        const n = base + day * 1000 + hour * 37 + j * 11;
        const merchant = pick(MERCHANTS, n);
        const amount = Math.round((8 + (n % 175) + (hour % 5) * 3) * 100) / 100;

        // Decline pattern: post-10PM bump + a small issuer outage window around 02:00
        const late = hour >= 22 ? 0.18 : 0.07;
        const outage = hour === 2 ? 0.12 : 0;
        const declineProb = late + outage + (merchant.id === "m_summit" ? 0.03 : 0);
        const approved = (n % 1000) / 1000 > declineProb;
        const decline = pick(DECLINES, n);

        rows.push({
          id: `auth_${network}_${day}_${hour}_${j}`,
          timestampISO: isoUTC(y, m, day, hour, j * 20, 10),
          network,
          reportType: "Authorization",
          merchantId: merchant.id,
          merchantName: merchant.name,
          merchantCountry: merchant.country,
          mcc: merchant.mcc,
          entryMode: pick(ENTRY_MODES, n),
          currency: "USD",
          amount,
          approved,
          responseCode: approved ? "00" : decline.code,
          declineReason: approved ? undefined : decline.reason,
          // Tiny, deterministic chargeback flag for demo queries.
          chargebackFlag: !approved ? false : (n % 97 === 0),
        });
      }
    }
  }
  return rows;
}

function makeSettlementRows(seed: Seed, network: CardNetwork, y = 2025, m = 12) {
  const base = stableHash(seed + "settle" + network);
  const rows: SettlementRow[] = [];
  // 14 days daily settlement batches.
  for (let day = 11; day <= 24; day++) {
    const n = base + day * 991;
    const merchant = pick(MERCHANTS, n);

    const txCount = 180 + (n % 120);
    const crossBorder = merchant.country !== "US" ? true : (n % 7 === 0);

    // Interchange trending upward slightly over the period
    const trend = (day - 11) * 0.0006;
    const feeRate = 0.018 + trend + (crossBorder ? 0.004 : 0);

    const grossAmount =
      Math.round((txCount * (22 + (n % 15) + (crossBorder ? 6 : 0))) * 100) / 100;
    const interchangeFees = Math.round(grossAmount * feeRate * 100) / 100;
    const netAmount = Math.round((grossAmount - interchangeFees) * 100) / 100;

    // Settlement delays correlate with cross-border (demo insight)
    const settlementDelayDays = (crossBorder ? (n % 3) + 1 : (n % 9 === 0 ? 1 : 0)) as
      | 0
      | 1
      | 2
      | 3;

    rows.push({
      id: `stl_${network}_${day}`,
      settlementDateISO: isoUTC(y, m, day, 9, 0, 0),
      network,
      reportType: "Settlement",
      merchantId: merchant.id,
      merchantName: merchant.name,
      merchantCountry: merchant.country,
      currency: "USD",
      txCount,
      grossAmount,
      interchangeFees,
      netAmount,
      crossBorder,
      settlementDelayDays,
    });
  }
  return rows;
}

function reportRangeForAuth() {
  return { startISO: isoUTC(2025, 12, 18), endISO: isoUTC(2025, 12, 24, 23, 59, 59) };
}

function reportRangeForSettlement() {
  return { startISO: isoUTC(2025, 12, 11), endISO: isoUTC(2025, 12, 24, 23, 59, 59) };
}

export const MOCK_REPORTS: Report[] = [
  {
    id: "r_auth_visa_dec",
    name: "Authorization Summary — Dec 18–24 (Visa)",
    type: "Authorization",
    network: "Visa",
    dateRange: reportRangeForAuth(),
    rows: makeAuthRows("payscope_demo", "Visa"),
  },
  {
    id: "r_auth_mc_dec",
    name: "Authorization Summary — Dec 18–24 (Mastercard)",
    type: "Authorization",
    network: "Mastercard",
    dateRange: reportRangeForAuth(),
    rows: makeAuthRows("payscope_demo", "Mastercard"),
  },
  {
    id: "r_settle_visa_dec",
    name: "Settlement Batch — Dec 11–24 (Visa)",
    type: "Settlement",
    network: "Visa",
    dateRange: reportRangeForSettlement(),
    rows: makeSettlementRows("payscope_demo", "Visa"),
  },
  {
    id: "r_settle_mc_dec",
    name: "Settlement Batch — Dec 11–24 (Mastercard)",
    type: "Settlement",
    network: "Mastercard",
    dateRange: reportRangeForSettlement(),
    rows: makeSettlementRows("payscope_demo", "Mastercard"),
  },
];

export const MOCK_REPORT_SUMMARIES: ReportSummary[] = MOCK_REPORTS.map((r) => ({
  id: r.id,
  name: r.name,
  type: r.type,
  network: r.network,
  dateRange: r.dateRange,
  rowCount: r.rows.length,
}));

export function getReportById(reportId: string) {
  return MOCK_REPORTS.find((r) => r.id === reportId) ?? null;
}

export function inferReportTypeFromFilename(filename: string): ReportType {
  const f = filename.toLowerCase();
  if (f.includes("settle") || f.includes("recon") || f.includes("batch")) return "Settlement";
  return "Authorization";
}


