## PayScope (Hackathon Demo)

**PayScope** is a Visa-style fintech analytics demo: an AI-powered reporting intelligence layer that sits on top of existing Visa/Mastercard payment reports (authorization + settlement), transforming static reports into interactive dashboards and conversational insights.

**Important**: PayScope is **NOT** a payment system. Auth + AI are mocked and deterministic for demo impact.

### Tech stack (strict)

- Next.js 16 (App Router)
- TypeScript (strict)
- Tailwind CSS
- Recharts (charts)
- Mock auth + mock AI routes (AI-ready structure)

### Getting started

First, run the development server:

```bash
npm run dev
```

Then open `http://localhost:3000`.

### Information architecture (mandatory)

- `/` landing
- `/dashboard` (redirects to insights)
- `/dashboard/reports`
- `/dashboard/insights`
- `/dashboard/chat`

### Mock AI architecture (AI-ready)

- `POST /api/reports/parse` – deterministic “parsing” of uploaded metadata → returns a report
- `POST /api/insights` – deterministic KPI + chart data + insight cards
- `POST /api/chat` – deterministic, analyst-style responses grounded in computed metrics

### Mock data

- `src/lib/mockReports.ts` – realistic Visa/Mastercard authorization + settlement data generators
- `src/lib/analytics.ts` – KPI + chart derivations used by both UI and API routes

### Key folders

- `src/app/` – App Router pages + API routes
- `src/components/` – UI + layout components (fintech-grade, desktop-first)
- `src/lib/` – types, mock data, analytics utilities

### Demo tips

- Start at `/` → click **View Demo Dashboard**
- Use `/dashboard/reports` to “upload” a file (mock) and select reports
- Use `/dashboard/insights` for KPIs + charts + AI insight cards
- Use `/dashboard/chat` for analyst-style Q&A with example prompts

