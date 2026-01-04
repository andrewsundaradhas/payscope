import { NextResponse } from "next/server";
import type { CardNetwork, Report } from "@/lib/types";
import { inferReportTypeFromFilename, MOCK_REPORTS } from "@/lib/mockReports";

// AI-ready (mock): This endpoint accepts structured metadata and returns a deterministic parse result.
// In a future RAG setup, this would run real parsing (CSV/PDF) and write to a vector store.

type ParseRequest = {
  filename: string;
  networkHint?: CardNetwork;
};

function stableIdFromString(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h.toString(16).slice(0, 8);
}

export async function POST(req: Request) {
  const body = (await req.json()) as ParseRequest;
  const filename = body.filename ?? "uploaded_report";
  const network: CardNetwork = body.networkHint ?? (filename.toLowerCase().includes("master") ? "Mastercard" : "Visa");
  const type = inferReportTypeFromFilename(filename);

  const template =
    MOCK_REPORTS.find((r) => r.type === type && r.network === network) ??
    MOCK_REPORTS[0];

  const id = `upl_${stableIdFromString(`${filename}:${network}:${type}`)}`;
  const report: Report = {
    ...template,
    id,
    name: `Parsed Upload — ${filename.replace(/\.[^/.]+$/, "")} (${network})`,
  };

  return NextResponse.json({ report });
}


