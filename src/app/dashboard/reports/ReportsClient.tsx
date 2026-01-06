"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import type { AuthRow, Report, SettlementRow } from "@/lib/types";
import {
  computeAuthKpis,
  computeSettlementKpis,
  formatInt,
  formatMoneyUSD,
  formatPercent,
} from "@/lib/analytics";
import { cn } from "@/lib/utils";

type ParseResponse = { report: Report };

// Metric card with gradient accent
function Metric({ 
  label, 
  value, 
  accent = "emerald" 
}: { 
  label: string; 
  value: string;
  accent?: "emerald" | "amber" | "rose" | "sky";
}) {
  const accents = {
    emerald: "from-emerald-500/10 to-teal-500/5 border-emerald-200/60",
    amber: "from-amber-500/10 to-orange-500/5 border-amber-200/60",
    rose: "from-rose-500/10 to-pink-500/5 border-rose-200/60",
    sky: "from-sky-500/10 to-blue-500/5 border-sky-200/60",
  };
  
  return (
    <div className={cn(
      "relative overflow-hidden rounded-2xl border bg-gradient-to-br px-5 py-4 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg",
      accents[accent]
    )}>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{label}</div>
      <div className="mt-2 font-mono text-2xl font-bold tracking-tight text-slate-800">{value}</div>
      <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-white/40 blur-2xl" />
    </div>
  );
}

function formatISODate(iso: string) {
  return iso.slice(0, 10);
}

export default function ReportsClient({ sample }: { sample: boolean }) {
  const { reportSummaries, selectedReportId, setSelectedReportId, selectedReport, addReport } =
    useDashboardStore();

  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);

  useEffect(() => {
    // Demo: if user clicked "Upload Sample Report" from landing.
    if (!sample) return;
    // No-op: we already ship pre-parsed reports; this just sets a sensible selection.
    const preferred =
      reportSummaries.find((r) => r.type === "Authorization" && r.network === "Visa") ??
      reportSummaries[0];
    if (preferred) setSelectedReportId(preferred.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sample]);

  const metrics = useMemo(() => {
    if (!selectedReport) return null;
    if (selectedReport.type === "Authorization") {
      const rows = selectedReport.rows as AuthRow[];
      const k = computeAuthKpis(rows);
      return {
        totalTx: formatInt(k.total),
        approvalRate: formatPercent(k.approvalRate),
        declineRate: formatPercent(k.declineRate),
        totalSettlementAmount: "—",
      };
    }
    const rows = selectedReport.rows as SettlementRow[];
    const k = computeSettlementKpis(rows);
    return {
      totalTx: formatInt(k.tx),
      approvalRate: "—",
      declineRate: "—",
      totalSettlementAmount: formatMoneyUSD(k.settlementVolume),
    };
  }, [selectedReport]);

  const previewRows = useMemo(() => {
    if (!selectedReport) return [];
    return selectedReport.rows.slice(0, 14);
  }, [selectedReport]);

  async function onUploadMock(file: File) {
    setUploading(true);
    setUploadErr(null);
    try {
      const res = await fetch("/api/reports/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
        }),
      });
      if (!res.ok) throw new Error(`Parse failed (${res.status})`);
      const data = (await res.json()) as ParseResponse;
      addReport(data.report);
    } catch (e) {
      setUploadErr(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30 p-6 lg:p-8">
      {/* Decorative background elements */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 top-20 h-80 w-80 rounded-full bg-emerald-200/20 blur-3xl" />
        <div className="absolute -right-40 top-60 h-96 w-96 rounded-full bg-sky-200/20 blur-3xl" />
        <div className="absolute bottom-20 left-1/3 h-72 w-72 rounded-full bg-amber-200/15 blur-3xl" />
      </div>
      
      <div className="relative grid gap-8 lg:grid-cols-12">
        {/* Left Panel - Reports List */}
        <div className="lg:col-span-4">
          <div className="sticky top-6 space-y-6">
            {/* Upload Card */}
            <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
              <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold tracking-tight text-slate-800">Parsed Reports</h2>
                  <span className="rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white shadow-lg shadow-emerald-500/25">
                    Mock
                  </span>
                </div>
              </div>
              
              <div className="p-5 space-y-5">
                {/* Upload Section */}
                <div className="relative overflow-hidden rounded-2xl border border-dashed border-slate-300 bg-gradient-to-br from-slate-50 to-white p-5">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.05),transparent_50%)]" />
                  <div className="relative">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/30">
                        <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-800">Upload report</div>
                        <div className="text-[11px] text-slate-500">CSV / Excel / PDF</div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex items-center gap-3">
                      <label className={cn("group flex-1", uploading && "opacity-70")}>
                        <input
                          type="file"
                          className="hidden"
                          accept=".csv,.xlsx,.pdf"
                          disabled={uploading}
                          onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (f) void onUploadMock(f);
                            e.currentTarget.value = "";
                          }}
                        />
                        <span className="flex h-11 w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-sm font-semibold text-white shadow-lg shadow-emerald-500/30 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-500/40 group-hover:-translate-y-0.5">
                          {uploading ? (
                            <>
                              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                              Parsing…
                            </>
                          ) : (
                            <>
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                              </svg>
                              Choose file
                            </>
                          )}
                        </span>
                      </label>
                      <Button
                        type="button"
                        disabled={uploading}
                        onClick={() =>
                          void onUploadMock(
                            new File(["mock"], "Visa_Authorization_Report_Dec.csv", {
                              type: "text/csv",
                            }),
                          )
                        }
                        className="h-11 rounded-xl border-2 border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition-all duration-300 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700"
                      >
                        Use sample
                      </Button>
                    </div>
                    
                    {uploadErr && (
                      <div className="mt-3 flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-600">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {uploadErr}
                      </div>
                    )}
                  </div>
                </div>

                {/* Reports List */}
                <div className="space-y-2">
                  {reportSummaries.map((r) => {
                    const active = r.id === selectedReportId;
                    const isAuth = r.type === "Authorization";
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => setSelectedReportId(r.id)}
                        className={cn(
                          "group relative w-full overflow-hidden rounded-2xl border p-4 text-left transition-all duration-300",
                          active 
                            ? "border-emerald-300 bg-gradient-to-br from-emerald-50 to-teal-50/50 shadow-lg shadow-emerald-500/10" 
                            : "border-slate-200/80 bg-white/60 hover:border-slate-300 hover:bg-white hover:shadow-md",
                        )}
                      >
                        {active && (
                          <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-emerald-500 to-teal-500" />
                        )}
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <div className={cn(
                                "flex h-7 w-7 items-center justify-center rounded-lg",
                                isAuth 
                                  ? "bg-gradient-to-br from-sky-100 to-blue-100 text-sky-600" 
                                  : "bg-gradient-to-br from-amber-100 to-orange-100 text-amber-600"
                              )}>
                                {isAuth ? (
                                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                  </svg>
                                ) : (
                                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                )}
                              </div>
                              <span className="truncate text-sm font-bold text-slate-800">
                                {r.type}
                              </span>
                            </div>
                            <div className="mt-1.5 flex items-center gap-2 pl-9 text-xs text-slate-500">
                              <span className={cn(
                                "rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                                r.network === "Visa" 
                                  ? "bg-blue-100 text-blue-700" 
                                  : "bg-orange-100 text-orange-700"
                              )}>
                                {r.network}
                              </span>
                              <span className="text-slate-400">•</span>
                              <span className="font-mono text-[11px]">
                                {formatISODate(r.dateRange.startISO)} → {formatISODate(r.dateRange.endISO)}
                              </span>
                            </div>
                          </div>
                          <span className={cn(
                            "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold tabular-nums",
                            active
                              ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/30"
                              : "bg-slate-100 text-slate-600 group-hover:bg-slate-200"
                          )}>
                            {formatInt(r.rowCount)}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Report Details */}
        <div className="lg:col-span-8 space-y-6">
          {/* Summary Metrics */}
          <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
            <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 shadow-lg shadow-sky-500/30">
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h2 className="text-lg font-bold tracking-tight text-slate-800">Report Summary</h2>
              </div>
            </div>
            <div className="p-6">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Metric label="Total transactions" value={metrics?.totalTx ?? "—"} accent="sky" />
                <Metric label="Approval rate" value={metrics?.approvalRate ?? "—"} accent="emerald" />
                <Metric label="Decline rate" value={metrics?.declineRate ?? "—"} accent="rose" />
                <Metric label="Settlement amount" value={metrics?.totalSettlementAmount ?? "—"} accent="amber" />
              </div>
            </div>
          </div>

          {/* Table Preview */}
          <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
            <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/30">
                    <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h2 className="text-lg font-bold tracking-tight text-slate-800">Table Preview</h2>
                </div>
                {selectedReport && (
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                    Showing first {Math.min(14, selectedReport.rows.length)} rows
                  </span>
                )}
              </div>
            </div>
            <div className="p-6">
              {!selectedReport ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200">
                    <svg className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="mt-4 text-sm font-medium text-slate-500">Select a report to preview</p>
                  <p className="mt-1 text-xs text-slate-400">Choose from the list on the left</p>
                </div>
              ) : selectedReport.type === "Authorization" ? (
                <AuthPreview rows={previewRows as AuthRow[]} />
              ) : (
                <SettlementPreview rows={previewRows as SettlementRow[]} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TableShell({
  headers,
  children,
}: {
  headers: string[];
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-[13px]">
          <thead>
            <tr className="bg-gradient-to-r from-slate-50 to-slate-100/50">
              {headers.map((h, i) => (
                <th
                  key={h}
                  className={cn(
                    "whitespace-nowrap px-4 py-3.5 text-[11px] font-bold uppercase tracking-wider text-slate-500",
                    i === 0 && "pl-5",
                    i === headers.length - 1 && "pr-5"
                  )}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">{children}</tbody>
        </table>
      </div>
    </div>
  );
}

function AuthPreview({ rows }: { rows: AuthRow[] }) {
  return (
    <TableShell
      headers={[
        "Timestamp",
        "Network",
        "Merchant",
        "MCC",
        "Entry mode",
        "Amount",
        "Response",
        "Approved",
      ]}
    >
      {rows.map((r, idx) => (
        <tr 
          key={r.id} 
          className={cn(
            "transition-colors duration-150 hover:bg-emerald-50/50",
            idx % 2 === 0 ? "bg-white" : "bg-slate-50/30"
          )}
        >
          <td className="whitespace-nowrap px-4 py-3 pl-5 font-mono text-xs text-slate-500">
            {r.timestampISO.replace("T", " ").slice(0, 16)}Z
          </td>
          <td className="px-4 py-3">
            <span className={cn(
              "inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold",
              r.network === "Visa" 
                ? "bg-blue-100 text-blue-700" 
                : "bg-orange-100 text-orange-700"
            )}>
              {r.network}
            </span>
          </td>
          <td className="px-4 py-3 font-medium text-slate-800">{r.merchantName}</td>
          <td className="px-4 py-3 font-mono text-xs text-slate-500">{r.mcc}</td>
          <td className="px-4 py-3">
            <span className="inline-flex items-center rounded-lg bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
              {r.entryMode}
            </span>
          </td>
          <td className="px-4 py-3 font-mono font-semibold text-slate-800">{formatMoneyUSD(r.amount)}</td>
          <td className="px-4 py-3">
            <span className="font-mono text-xs text-slate-500">{r.responseCode}</span>
            {!r.approved && r.declineReason && (
              <span className="ml-1.5 text-[10px] text-rose-500">({r.declineReason})</span>
            )}
          </td>
          <td className="px-4 py-3 pr-5">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold shadow-sm",
                r.approved
                  ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-emerald-500/25"
                  : "bg-gradient-to-r from-rose-500 to-pink-500 text-white shadow-rose-500/25",
              )}
            >
              {r.approved ? (
                <>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                  Yes
                </>
              ) : (
                <>
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  No
                </>
              )}
            </span>
          </td>
        </tr>
      ))}
    </TableShell>
  );
}

function SettlementPreview({ rows }: { rows: SettlementRow[] }) {
  return (
    <TableShell
      headers={[
        "Settlement date",
        "Network",
        "Merchant",
        "Tx count",
        "Gross",
        "Interchange",
        "Net",
        "Delay",
      ]}
    >
      {rows.map((r, idx) => (
        <tr 
          key={r.id} 
          className={cn(
            "transition-colors duration-150 hover:bg-amber-50/50",
            idx % 2 === 0 ? "bg-white" : "bg-slate-50/30"
          )}
        >
          <td className="whitespace-nowrap px-4 py-3 pl-5 font-mono text-xs text-slate-500">
            {formatISODate(r.settlementDateISO)}
          </td>
          <td className="px-4 py-3">
            <span className={cn(
              "inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold",
              r.network === "Visa" 
                ? "bg-blue-100 text-blue-700" 
                : "bg-orange-100 text-orange-700"
            )}>
              {r.network}
            </span>
          </td>
          <td className="px-4 py-3 font-medium text-slate-800">{r.merchantName}</td>
          <td className="px-4 py-3">
            <span className="inline-flex items-center rounded-lg bg-sky-100 px-2 py-0.5 font-mono text-xs font-bold text-sky-700">
              {formatInt(r.txCount)}
            </span>
          </td>
          <td className="px-4 py-3 font-mono font-semibold text-emerald-600">{formatMoneyUSD(r.grossAmount)}</td>
          <td className="px-4 py-3 font-mono text-xs text-rose-500">-{formatMoneyUSD(r.interchangeFees)}</td>
          <td className="px-4 py-3 font-mono font-bold text-slate-800">{formatMoneyUSD(r.netAmount)}</td>
          <td className="px-4 py-3 pr-5">
            <span className={cn(
              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold",
              r.settlementDelayDays <= 1 
                ? "bg-emerald-100 text-emerald-700"
                : r.settlementDelayDays <= 3
                  ? "bg-amber-100 text-amber-700"
                  : "bg-rose-100 text-rose-700"
            )}>
              {r.settlementDelayDays}d
            </span>
          </td>
        </tr>
      ))}
    </TableShell>
  );
}


