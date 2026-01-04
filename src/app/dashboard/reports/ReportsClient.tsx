"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3">
      <div className="text-xs font-semibold text-white/60">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
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
    <div className="grid gap-6 lg:grid-cols-12">
      <div className="lg:col-span-4">
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Parsed Reports</CardTitle>
            <Badge>Mock</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="rounded-lg border border-white/10 bg-white/5 p-4">
              <div className="text-sm font-semibold text-white">Upload report</div>
              <div className="mt-1 text-xs text-white/60">
                CSV / Excel / PDF supported (mocked). Uses `/api/reports/parse`.
              </div>
              <div className="mt-3 flex items-center gap-3">
                <label className={cn("inline-flex", uploading && "opacity-70")}>
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
                  <span className="inline-flex h-9 cursor-pointer items-center rounded-md bg-[var(--ps-blue)] px-3 text-sm font-semibold text-white hover:bg-[var(--ps-blue-2)]">
                    {uploading ? "Parsing…" : "Choose file"}
                  </span>
                </label>
                <Button
                  type="button"
                  variant="secondary"
                  disabled={uploading}
                  onClick={() =>
                    void onUploadMock(
                      new File(["mock"], "Visa_Authorization_Report_Dec.csv", {
                        type: "text/csv",
                      }),
                    )
                  }
                >
                  Use sample
                </Button>
              </div>
              {uploadErr ? (
                <div className="mt-3 text-xs font-semibold text-[var(--ps-bad)]">
                  {uploadErr}
                </div>
              ) : null}
            </div>

            <div className="space-y-2">
              {reportSummaries.map((r) => {
                const active = r.id === selectedReportId;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setSelectedReportId(r.id)}
                    className={cn(
                      "w-full rounded-lg border border-white/10 px-4 py-3 text-left transition",
                      active ? "bg-white/8" : "bg-white/5 hover:bg-white/8",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-white">
                          {r.type}
                        </div>
                        <div className="mt-0.5 truncate text-xs text-white/60">
                          {r.network} · {formatISODate(r.dateRange.startISO)} →{" "}
                          {formatISODate(r.dateRange.endISO)}
                        </div>
                      </div>
                      <Badge className="shrink-0">{formatInt(r.rowCount)} rows</Badge>
                    </div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="lg:col-span-8">
        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Report Summary</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Metric label="Total transactions" value={metrics?.totalTx ?? "—"} />
              <Metric label="Approval rate" value={metrics?.approvalRate ?? "—"} />
              <Metric label="Decline rate" value={metrics?.declineRate ?? "—"} />
              <Metric
                label="Total settlement amount"
                value={metrics?.totalSettlementAmount ?? "—"}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex items-center justify-between">
              <CardTitle>Table Preview</CardTitle>
              {selectedReport ? (
                <div className="text-xs text-white/60">
                  Showing first {Math.min(14, selectedReport.rows.length)} rows
                </div>
              ) : null}
            </CardHeader>
            <CardContent>
              {!selectedReport ? (
                <div className="text-sm text-white/70">
                  Select a report to preview.
                </div>
              ) : selectedReport.type === "Authorization" ? (
                <AuthPreview rows={previewRows as AuthRow[]} />
              ) : (
                <SettlementPreview rows={previewRows as SettlementRow[]} />
              )}
            </CardContent>
          </Card>
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
    <div className="overflow-hidden rounded-lg border border-white/10">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="bg-white/5">
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                className="border-b border-white/10 px-3 py-2 font-semibold text-white/70"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-[var(--ps-panel-2)]">{children}</tbody>
      </table>
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
      {rows.map((r) => (
        <tr key={r.id} className="border-t border-white/10">
          <td className="px-3 py-2 text-white/75">
            {r.timestampISO.replace("T", " ").slice(0, 16)}Z
          </td>
          <td className="px-3 py-2 text-white/75">{r.network}</td>
          <td className="px-3 py-2 text-white/90">{r.merchantName}</td>
          <td className="px-3 py-2 text-white/75">{r.mcc}</td>
          <td className="px-3 py-2 text-white/75">{r.entryMode}</td>
          <td className="px-3 py-2 text-white/90">{formatMoneyUSD(r.amount)}</td>
          <td className="px-3 py-2 text-white/75">
            {r.responseCode}
            {!r.approved && r.declineReason ? (
              <span className="ml-2 text-white/50">({r.declineReason})</span>
            ) : null}
          </td>
          <td className="px-3 py-2">
            <span
              className={cn(
                "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold",
                r.approved
                  ? "bg-[rgba(42,194,143,0.18)] text-white"
                  : "bg-[rgba(255,91,107,0.18)] text-white",
              )}
            >
              {r.approved ? "Yes" : "No"}
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
        "Delay (days)",
      ]}
    >
      {rows.map((r) => (
        <tr key={r.id} className="border-t border-white/10">
          <td className="px-3 py-2 text-white/75">{formatISODate(r.settlementDateISO)}</td>
          <td className="px-3 py-2 text-white/75">{r.network}</td>
          <td className="px-3 py-2 text-white/90">{r.merchantName}</td>
          <td className="px-3 py-2 text-white/90">{formatInt(r.txCount)}</td>
          <td className="px-3 py-2 text-white/90">{formatMoneyUSD(r.grossAmount)}</td>
          <td className="px-3 py-2 text-white/90">{formatMoneyUSD(r.interchangeFees)}</td>
          <td className="px-3 py-2 text-white/90">{formatMoneyUSD(r.netAmount)}</td>
          <td className="px-3 py-2 text-white/75">{r.settlementDelayDays}</td>
        </tr>
      ))}
    </TableShell>
  );
}


