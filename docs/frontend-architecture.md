# Frontend Architecture (PayScope)

This document explains how the PayScope **frontend** is structured and how data flows through the app (UI → API routes → shared analytics).

## Stack

- **Next.js 16** (App Router) + **TypeScript (strict)**
- **React 19**
- **Tailwind CSS v4** (via `@tailwindcss/postcss`) + CSS variables design tokens
- **Recharts** for charts
- **Deterministic mock data + mock AI** (demo-friendly, AI-ready structure)

## High-level structure

- **Routing + API routes**: `src/app/`
- **UI components**: `src/components/`
- **Business logic + mock datasets**: `src/lib/`

Key folders:

- `src/app/`
  - `page.tsx`: landing page
  - `dashboard/*`: dashboard pages + shell layout
  - `api/*`: internal API route handlers (mock AI-ready endpoints)
- `src/components/layout/*`: `DashboardShell`, `Sidebar`, `TopBar`
- `src/components/ui/*`: small design-system primitives (`Button`, `Card`, `Badge`, `Select`)
- `src/lib/`
  - `types.ts`: shared request/response + domain types
  - `mockReports.ts`: deterministic data generator + in-memory reports
  - `analytics.ts`: metrics, filtering, chart derivations (used by UI and API routes)
  - `utils.ts`: `cn()` for Tailwind class merging

## Routes (information architecture)

- `/`: landing
- `/dashboard`: redirects → `/dashboard/insights`
- `/dashboard/reports`: select “parsed” reports + mock upload → adds a report to the in-memory dashboard store
- `/dashboard/insights`: KPIs + charts from `/api/insights`
- `/dashboard/chat`: chat UI backed by `/api/chat`

## State management

State is intentionally minimal and local:

- `src/app/dashboard/DashboardProvider.tsx` defines a React Context store.
- Store contains:
  - `reports` and `reportSummaries` (seeded from `MOCK_REPORTS`)
  - `selectedReportId`
  - `filters` (`network`, `rangeDays`)
  - `addReport(report)` (used by mock upload flow)
  - `selectedReport` derived via `useMemo`

The provider is mounted once in `DashboardShell`, so all dashboard pages share the same in-memory state for the session.

## Data flow (end-to-end)

### 1) Report selection / “upload”

- UI: `src/app/dashboard/reports/ReportsClient.tsx`
  - On “upload”, sends a POST to `/api/reports/parse` with `{ filename }`
  - Response includes a `report` (copied from a template in `MOCK_REPORTS`)
  - Calls `addReport(report)` to prepend into the store and select it

### 2) Insights

- UI: `src/app/dashboard/insights/page.tsx`
  - `useEffect` triggers when `selectedReportId` or `filters` changes
  - POST `/api/insights` with `{ reportId, filters }`
- API: `src/app/api/insights/route.ts`
  - Loads the selected report from `MOCK_REPORTS`
  - Uses `filterReportRows()` + `computeAuthKpis()` / `computeSettlementKpis()`
  - Generates deterministic:
    - KPIs
    - Charts (`transactionsOverTime`, `declinesByHour`, `networkComparison`)
    - Insight cards (rule-based narratives grounded in computed metrics)

### 3) Chat

- UI: `src/app/dashboard/chat/page.tsx`
  - POST `/api/chat` with `{ reportId, question, filters, thread? }`
- API: `src/app/api/chat/route.ts`
  - Rule-based intent routing (settlement drop, network approval comparison, chargebacks, default summary)
  - Always returns a structured response:
    - `answer` (string)
    - `metricsUsed` (array of label/value pairs)
    - `followups` (string suggestions)

## Internal API contracts

All routes are **internal Next.js route handlers** under `src/app/api/*`.

### `POST /api/reports/parse`

- **Request**:
  - `{ filename: string; networkHint?: "Visa" | "Mastercard" }`
- **Response**:
  - `{ report: Report }`
- **Notes**:
  - Deterministically chooses a template report from `MOCK_REPORTS` based on filename + network

### `POST /api/insights`

- **Request**:
  - `{ reportId: string; filters: { network: "All"|"Visa"|"Mastercard"; rangeDays: 7|30|90 } }`
- **Response**: `InsightsResponse` (see `src/lib/types.ts`)

### `POST /api/chat`

- **Request**: `ChatRequest` (see `src/lib/types.ts`)
- **Response**: `ChatResponse` (see `src/lib/types.ts`)

## Styling system

- Global tokens live in `src/app/globals.css` as CSS variables (`--ps-*`).
- Tailwind is used mostly as utility composition, with the palette expressed via CSS variables:
  - `bg-[var(--ps-panel)]`, `text-[color:var(--ps-fg)]`, etc.
- UI primitives (`Button`, `Card`, etc.) enforce consistent focus/hover/disabled behavior.

## Notes / risks / improvement ideas (optional)

- **Type signature (Next.js)**: Keep page prop types aligned with Next’s expectations (e.g., `searchParams` as an object).
- **API error UX**: current pages do basic `res.ok` checks; consider showing richer error states and retry UI.
- **Thread handling**: chat sends a `thread` field but the API doesn’t currently use it; if you later add conversational grounding, update client to send the latest thread snapshot.
- **Real backend integration**: repo includes a Python backend (`/backend`), but the frontend currently uses only Next API routes and mock data; if you switch to the backend service, centralize the API client and add env-based base URLs.




