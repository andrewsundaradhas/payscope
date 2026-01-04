import { Suspense } from "react";
import ReportsClient from "@/app/dashboard/reports/ReportsClient";

export default async function ReportsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) ?? {};
  const sample = sp.sample === "1";
  return (
    <Suspense fallback={<div className="text-sm text-[color:var(--ps-muted)]">Loading…</div>}>
      <ReportsClient sample={sample} />
    </Suspense>
  );
}


