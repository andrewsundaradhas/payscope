export type CardNetwork = "Visa" | "Mastercard";
export type CardNetworkFilter = CardNetwork | "All";
export type ReportType = "Authorization" | "Settlement";

export type DateRangePreset = 7 | 30 | 90;

export type ReportDateRange = {
  startISO: string; // inclusive
  endISO: string; // inclusive
};

export type ReportFilters = {
  network: CardNetworkFilter;
  rangeDays: DateRangePreset;
};

export type AuthRow = {
  id: string;
  timestampISO: string;
  network: CardNetwork;
  reportType: "Authorization";
  merchantId: string;
  merchantName: string;
  merchantCountry: string; // ISO2-ish, e.g. "US"
  mcc: string;
  entryMode: "Chip" | "Contactless" | "Ecommerce" | "Magstripe";
  currency: "USD";
  amount: number;
  approved: boolean;
  responseCode: string; // e.g. "00", "05"
  declineReason?: string;
  chargebackFlag: boolean;
};

export type SettlementRow = {
  id: string;
  settlementDateISO: string;
  network: CardNetwork;
  reportType: "Settlement";
  merchantId: string;
  merchantName: string;
  merchantCountry: string;
  currency: "USD";
  txCount: number;
  grossAmount: number;
  interchangeFees: number;
  netAmount: number;
  crossBorder: boolean;
  settlementDelayDays: 0 | 1 | 2 | 3;
};

export type Report = {
  id: string;
  name: string;
  type: ReportType;
  network: CardNetwork;
  dateRange: ReportDateRange;
  rows: AuthRow[] | SettlementRow[];
};

export type ReportSummary = Omit<Report, "rows"> & {
  rowCount: number;
};

export type Kpi = {
  label: string;
  value: string;
  delta?: string;
  tone?: "neutral" | "good" | "warn" | "bad";
};

export type InsightCard = {
  id: string;
  title: string;
  narrative: string;
  supportingMetrics: Array<{ label: string; value: string }>;
  severity: "info" | "watch" | "risk";
};

export type InsightsResponse = {
  kpis: Kpi[];
  charts: {
    transactionsOverTime: Array<{ dateISO: string; count: number }>;
    declinesByHour: Array<{ hour: number; declines: number }>;
    networkComparison: Array<{ label: string; visa: number; mastercard: number }>;
  };
  insightCards: InsightCard[];
};

export type ChatRequest = {
  reportId: string;
  question: string;
  filters: ReportFilters;
  thread?: Array<{ role: "user" | "assistant"; content: string }>;
};

export type ChatResponse = {
  answer: string;
  metricsUsed: Array<{ label: string; value: string }>;
  followups: string[];
};


