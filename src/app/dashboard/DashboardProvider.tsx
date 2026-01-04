"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type {
  Report,
  ReportFilters,
  ReportSummary,
} from "@/lib/types";
import { MOCK_REPORTS, MOCK_REPORT_SUMMARIES } from "@/lib/mockReports";

type DashboardStore = {
  reports: Report[];
  reportSummaries: ReportSummary[];
  selectedReportId: string;
  setSelectedReportId: (id: string) => void;
  filters: ReportFilters;
  setFilters: (next: ReportFilters) => void;
  addReport: (r: Report) => void;
  selectedReport: Report | null;
};

const Ctx = createContext<DashboardStore | null>(null);

export function DashboardProvider({
  children,
  initialSelectedReportId,
}: {
  children: React.ReactNode;
  initialSelectedReportId?: string;
}) {
  const [reports, setReports] = useState<Report[]>(MOCK_REPORTS);
  const [reportSummaries, setReportSummaries] =
    useState<ReportSummary[]>(MOCK_REPORT_SUMMARIES);

  const [selectedReportId, setSelectedReportId] = useState<string>(
    initialSelectedReportId ?? reportSummaries[0]?.id ?? "",
  );

  const [filters, setFilters] = useState<ReportFilters>({
    network: "All",
    rangeDays: 7,
  });

  const selectedReport = useMemo(
    () => reports.find((r) => r.id === selectedReportId) ?? null,
    [reports, selectedReportId],
  );

  const value = useMemo<DashboardStore>(
    () => ({
      reports,
      reportSummaries,
      selectedReportId,
      setSelectedReportId,
      filters,
      setFilters,
      addReport: (r) => {
        setReports((prev) => [r, ...prev]);
        setReportSummaries((prev) => [
          {
            id: r.id,
            name: r.name,
            type: r.type,
            network: r.network,
            dateRange: r.dateRange,
            rowCount: r.rows.length,
          },
          ...prev,
        ]);
        setSelectedReportId(r.id);
      },
      selectedReport,
    }),
    [reports, reportSummaries, selectedReportId, filters, selectedReport],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useDashboardStore() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useDashboardStore must be used within DashboardProvider");
  return v;
}


