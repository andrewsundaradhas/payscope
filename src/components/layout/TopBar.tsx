"use client";

import { useMemo } from "react";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import { Select } from "@/components/ui/Select";
import type { CardNetworkFilter, DateRangePreset } from "@/lib/types";

export function TopBar() {
  const {
    reportSummaries,
    selectedReportId,
    setSelectedReportId,
    filters,
    setFilters,
    selectedReport,
  } = useDashboardStore();

  const reportLabel = useMemo(() => {
    const r = reportSummaries.find((x) => x.id === selectedReportId);
    return r?.name ?? "Select report…";
  }, [reportSummaries, selectedReportId]);

  return (
    <header className="flex h-14 items-center justify-between border-b bg-[var(--ps-panel)] px-6">
      <div className="flex min-w-0 items-center gap-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-[color:var(--ps-subtle)]">
          Selected report
        </div>
        <div className="min-w-0 truncate text-sm font-semibold text-[color:var(--ps-fg)]">
          {reportLabel}
        </div>
        {selectedReport ? (
          <div className="hidden text-xs text-[color:var(--ps-subtle)] md:block">
            {selectedReport.type} · {selectedReport.network}
          </div>
        ) : null}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 md:flex">
          <div className="text-xs font-semibold uppercase tracking-wide text-[color:var(--ps-subtle)]">
            Report
          </div>
          <Select
            value={selectedReportId}
            onChange={(e) => setSelectedReportId(e.target.value)}
            className="w-[360px]"
          >
            {reportSummaries.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden text-xs font-semibold uppercase tracking-wide text-[color:var(--ps-subtle)] md:block">
            Date range
          </div>
          <Select
            value={filters.rangeDays}
            onChange={(e) =>
              setFilters({ ...filters, rangeDays: Number(e.target.value) as DateRangePreset })
            }
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden text-xs font-semibold uppercase tracking-wide text-[color:var(--ps-subtle)] md:block">
            Network
          </div>
          <Select
            value={filters.network}
            onChange={(e) =>
              setFilters({ ...filters, network: e.target.value as CardNetworkFilter })
            }
          >
            <option value="All">All</option>
            <option value="Visa">Visa</option>
            <option value="Mastercard">Mastercard</option>
          </Select>
        </div>
      </div>
    </header>
  );
}


