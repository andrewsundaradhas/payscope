/**
 * PayScope API Client
 * 
 * Connects frontend to FastAPI backend for:
 * - Insights generation
 * - Forecasting
 * - Cross-analysis (auth vs settlement)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --------------------------------------------------------------------------
// Types
// --------------------------------------------------------------------------

export type NetworkFilter = "All" | "Visa" | "Mastercard";

export interface ReportFilters {
  network: NetworkFilter;
  range_days: number;
}

export interface Kpi {
  label: string;
  value: string;
  delta?: string;
  tone: "neutral" | "good" | "warn" | "bad";
}

export interface SupportingMetric {
  label: string;
  value: string;
}

export interface InsightCard {
  id: string;
  title: string;
  narrative: string;
  supporting_metrics: SupportingMetric[];
  severity: "info" | "watch" | "risk";
}

export interface TransactionTimeSeries {
  date_iso: string;
  count: number;
}

export interface DeclinesByHour {
  hour: number;
  declines: number;
}

export interface NetworkComparison {
  label: string;
  visa: number;
  mastercard: number;
}

export interface ChartsData {
  transactions_over_time: TransactionTimeSeries[];
  declines_by_hour: DeclinesByHour[];
  network_comparison: NetworkComparison[];
}

export interface InsightsResponse {
  kpis: Kpi[];
  charts: ChartsData;
  insight_cards: InsightCard[];
}

export interface ForecastPoint {
  date_iso: string;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  metric: string;
  horizon_days: number;
  forecast: ForecastPoint[];
  trend: "up" | "down" | "stable";
  confidence: number;
  narrative: string;
}

export interface CrossAnalysisMetric {
  label: string;
  auth_value: string;
  settlement_value: string;
  variance: string;
  status: "aligned" | "watch" | "mismatch";
}

export interface CrossAnalysisResponse {
  auth_report_id: string;
  settlement_report_id: string;
  metrics: CrossAnalysisMetric[];
  insights: InsightCard[];
  reconciliation_rate: number;
  narrative: string;
}

export interface TrendData {
  direction: "up" | "down" | "stable";
  change_percent: number;
  period: string;
  confidence: number;
  anomaly_detected?: boolean;
  anomaly_description?: string;
}

export interface TrendsResponse {
  report_id: string;
  trends: Record<string, TrendData>;
}

// --------------------------------------------------------------------------
// API Functions
// --------------------------------------------------------------------------

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      errorData
    );
  }

  return response.json();
}

/**
 * Generate AI-powered insights from payment reports
 */
export async function generateInsights(
  reportId: string,
  filters: ReportFilters
): Promise<InsightsResponse> {
  return fetchApi<InsightsResponse>("/api/insights/generate", {
    method: "POST",
    body: JSON.stringify({
      report_id: reportId,
      filters,
    }),
  });
}

/**
 * Generate forecasts for a specific metric
 */
export async function generateForecast(
  reportId: string,
  metric: "transactions" | "settlement" | "declines" | "interchange",
  horizonDays: number = 30
): Promise<ForecastResponse> {
  return fetchApi<ForecastResponse>("/api/insights/forecast", {
    method: "POST",
    body: JSON.stringify({
      report_id: reportId,
      metric,
      horizon_days: horizonDays,
    }),
  });
}

/**
 * Perform cross-analysis between authorization and settlement reports
 */
export async function crossAnalysis(
  authReportId: string,
  settlementReportId: string,
  filters: ReportFilters
): Promise<CrossAnalysisResponse> {
  return fetchApi<CrossAnalysisResponse>("/api/insights/cross-analysis", {
    method: "POST",
    body: JSON.stringify({
      auth_report_id: authReportId,
      settlement_report_id: settlementReportId,
      filters,
    }),
  });
}

/**
 * Get trend analysis for a report
 */
export async function getTrends(
  reportId: string,
  metric: string = "all"
): Promise<TrendsResponse> {
  return fetchApi<TrendsResponse>(
    `/api/insights/trends/${reportId}?metric=${metric}`
  );
}

/**
 * Health check for the API
 */
export async function healthCheck(): Promise<{ ok: boolean }> {
  return fetchApi<{ ok: boolean }>("/health");
}

// --------------------------------------------------------------------------
// Utility Functions
// --------------------------------------------------------------------------

/**
 * Check if the FastAPI backend is available
 */
export async function isBackendAvailable(): Promise<boolean> {
  try {
    await healthCheck();
    return true;
  } catch {
    return false;
  }
}

// --------------------------------------------------------------------------
// Chat API
// --------------------------------------------------------------------------

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatFilters {
  network: NetworkFilter;
  range_days: number;
}

export interface ChatMetric {
  label: string;
  value: string;
}

export interface ChatApiResponse {
  answer: string;
  metrics_used: ChatMetric[];
  followups: string[];
  intent: string;
  confidence: number;
  sources: string[];
}

/**
 * Send a chat query to the RAG-based chat API
 */
export async function sendChatQuery(
  reportId: string,
  question: string,
  filters: ChatFilters,
  thread?: ChatMessage[]
): Promise<ChatApiResponse> {
  return fetchApi<ChatApiResponse>("/api/chat/query", {
    method: "POST",
    body: JSON.stringify({
      report_id: reportId,
      question,
      filters,
      thread,
    }),
  });
}

/**
 * Get example chat questions
 */
export async function getChatExamples(): Promise<Record<string, string[]>> {
  return fetchApi<Record<string, string[]>>("/api/chat/examples");
}

// --------------------------------------------------------------------------
// Reports API
// --------------------------------------------------------------------------

export interface ReportMetadata {
  report_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  checksum: string;
  upload_time: string;
  status: string;
  network?: string;
  report_type?: string;
}

export interface ReportSummary {
  report_id: string;
  name: string;
  type: string;
  network: string;
  row_count: number;
  date_range: { start: string; end: string };
  status: string;
}

/**
 * Upload a report file
 */
export async function uploadReport(file: File): Promise<ReportMetadata> {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await fetch(`${API_BASE_URL}/api/reports/upload`, {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    throw new ApiError("Upload failed", response.status);
  }
  
  return response.json();
}

/**
 * List all reports
 */
export async function listReports(): Promise<ReportSummary[]> {
  return fetchApi<ReportSummary[]>("/api/reports/list");
}

/**
 * Get report details
 */
export async function getReport(reportId: string): Promise<ReportMetadata> {
  return fetchApi<ReportMetadata>(`/api/reports/${reportId}`);
}

/**
 * Convert snake_case API response to camelCase for frontend compatibility
 */
export function transformInsightsResponse(response: InsightsResponse) {
  return {
    kpis: response.kpis.map((kpi) => ({
      label: kpi.label,
      value: kpi.value,
      delta: kpi.delta,
      tone: kpi.tone,
    })),
    charts: {
      transactionsOverTime: response.charts.transactions_over_time.map((d) => ({
        dateISO: d.date_iso,
        count: d.count,
      })),
      declinesByHour: response.charts.declines_by_hour,
      networkComparison: response.charts.network_comparison,
    },
    insightCards: response.insight_cards.map((card) => ({
      id: card.id,
      title: card.title,
      narrative: card.narrative,
      supportingMetrics: card.supporting_metrics,
      severity: card.severity,
    })),
  };
}

