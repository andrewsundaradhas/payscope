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
    <div className="rounded-lg border bg-[var(--ps-panel-2)] px-4 py-3">
      <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">{label}</div>
      <div className="mt-1 text-lg font-semibold text-[color:var(--ps-fg)]">{value}</div>
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
            <div className="rounded-lg border bg-[var(--ps-panel-2)] p-4">
              <div className="text-sm font-semibold text-[color:var(--ps-fg)]">Upload report</div>
              <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
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
                      "w-full rounded-lg border bg-[var(--ps-panel)] px-4 py-3 text-left transition",
                      active ? "ring-2 ring-[rgba(20,52,203,0.18)]" : "hover:bg-black/[0.03]",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-[color:var(--ps-fg)]">
                          {r.type}
                        </div>
                        <div className="mt-0.5 truncate text-xs text-[color:var(--ps-subtle)]">
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
                <div className="text-xs text-[color:var(--ps-subtle)]">
                  Showing first {Math.min(14, selectedReport.rows.length)} rows
                </div>
              ) : null}
            </CardHeader>
            <CardContent>
              {!selectedReport ? (
                <div className="text-sm text-[color:var(--ps-muted)]">
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
    <div className="overflow-hidden rounded-lg border bg-[var(--ps-panel)]">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="bg-[var(--ps-panel-2)]">
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                className="border-b px-3 py-2 font-semibold text-[color:var(--ps-subtle)]"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-[var(--ps-panel)]">{children}</tbody>
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
        <tr key={r.id} className="border-t">
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">
            {r.timestampISO.replace("T", " ").slice(0, 16)}Z
          </td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{r.network}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{r.merchantName}</td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{r.mcc}</td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{r.entryMode}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{formatMoneyUSD(r.amount)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">
            {r.responseCode}
            {!r.approved && r.declineReason ? (
              <span className="ml-2 text-[color:var(--ps-subtle)]">({r.declineReason})</span>
            ) : null}
          </td>
          <td className="px-3 py-2">
            <span
              className={cn(
                "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold",
                r.approved
                  ? "bg-[rgba(42,194,143,0.16)] text-[color:var(--ps-fg)]"
                  : "bg-[rgba(255,91,107,0.14)] text-[color:var(--ps-fg)]",
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
        <tr key={r.id} className="border-t">
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{formatISODate(r.settlementDateISO)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{r.network}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{r.merchantName}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{formatInt(r.txCount)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{formatMoneyUSD(r.grossAmount)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{formatMoneyUSD(r.interchangeFees)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-fg)]">{formatMoneyUSD(r.netAmount)}</td>
          <td className="px-3 py-2 text-[color:var(--ps-muted)]">{r.settlementDelayDays}</td>
        </tr>
      ))}
    </TableShell>
  );
}


