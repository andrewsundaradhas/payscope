"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ChatResponse } from "@/lib/types";
import { cn } from "@/lib/utils";
import { isBackendAvailable, sendChatQuery, type ChatApiResponse } from "@/lib/api";

type Msg = { role: "user" | "assistant"; content: string };

const EXAMPLES = [
  "Why did settlement amounts drop last week?",
  "Compare Visa vs Mastercard approval rates",
  "Which merchants have the highest chargebacks?",
  "What's the forecast for next month?",
  "Show me the decline patterns after 10 PM",
] as const;

export default function ChatPage() {
  const { selectedReportId, filters, selectedReport } = useDashboardStore();
  const [thread, setThread] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "I can analyze the selected report and explain trends like an internal payments analyst. Ask me about declines, settlement volume, interchange fees, forecasts, or network comparisons.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [useBackend, setUseBackend] = useState<boolean | null>(null);
  const [lastIntent, setLastIntent] = useState<string | null>(null);
  const [lastConfidence, setLastConfidence] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  // Check if FastAPI backend is available
  useEffect(() => {
    isBackendAvailable().then(setUseBackend);
  }, []);

  const canSend = selectedReportId && input.trim().length > 0 && !sending;

  const reportHint = useMemo(() => {
    if (!selectedReport) return "Select a report to enable chat.";
    return `${selectedReport.type} · ${selectedReport.network}`;
  }, [selectedReport]);

  async function send() {
    const question = input.trim();
    if (!question || !selectedReportId) return;
    setSending(true);
    setErr(null);
    setInput("");
    setThread((prev) => [...prev, { role: "user", content: question }]);

    try {
      let answer: string;
      let metricsUsed: Array<{ label: string; value: string }> = [];
      let followups: string[] = [];

      if (useBackend) {
        // Use FastAPI backend
        const response = await sendChatQuery(
          selectedReportId,
          question,
          {
            network: filters.network,
            range_days: filters.rangeDays,
          },
          thread.map((m) => ({ role: m.role, content: m.content }))
        );
        
        answer = response.answer;
        metricsUsed = response.metrics_used;
        followups = response.followups;
        setLastIntent(response.intent);
        setLastConfidence(response.confidence);
      } else {
        // Fallback to Next.js API route
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            reportId: selectedReportId,
            question,
            filters,
            thread,
          }),
        });
        if (!res.ok) throw new Error(`Chat failed (${res.status})`);
        const data = (await res.json()) as ChatResponse;
        answer = data.answer;
        metricsUsed = data.metricsUsed;
        followups = data.followups;
      }

      const appendix =
        metricsUsed.length === 0
          ? ""
          : `\n\n**Metrics referenced:**\n${metricsUsed
              .map((m) => `• ${m.label}: ${m.value}`)
              .join("\n")}`;

      const followupSection =
        followups.length === 0
          ? ""
          : `\n\n**Suggested follow-ups:**\n${followups.map((f) => `• ${f}`).join("\n")}`;

      setThread((prev) => [
        ...prev,
        { role: "assistant", content: `${answer}${appendix}${followupSection}` },
      ]);
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ behavior: "smooth" }));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Chat error");
      setThread((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't generate a response. Try again or switch to a different report.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-2xl font-semibold text-[color:var(--ps-fg)]">AI Chat Assistant</div>
          <div className="mt-1 text-sm text-[color:var(--ps-subtle)]">
            Natural language interaction with payment reports using RAG + multi-agent reasoning.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone="blue">
            {useBackend ? "FastAPI RAG" : "/api/chat"}
          </Badge>
          <Badge tone={useBackend ? "gold" : "neutral"}>
            {useBackend ? "AI-Powered" : "Mock"}
          </Badge>
          <Badge>{reportHint}</Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        <Card className="lg:col-span-8">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Conversation</CardTitle>
            <div className="flex items-center gap-2">
              {lastIntent && (
                <Badge tone="neutral" className="text-xs">
                  Intent: {lastIntent}
                </Badge>
              )}
              {lastConfidence && (
                <Badge tone="neutral" className="text-xs">
                  {(lastConfidence * 100).toFixed(0)}% confidence
                </Badge>
              )}
              {err ? (
                <div className="text-xs font-semibold text-[var(--ps-bad)]">{err}</div>
              ) : null}
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[520px] overflow-auto rounded-xl border bg-[var(--ps-panel-2)] p-4">
              <div className="space-y-3">
                {thread.map((m, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "max-w-[92%] rounded-xl border px-4 py-3 text-sm leading-6",
                      m.role === "user"
                        ? "ml-auto bg-[var(--ps-blue)] text-white"
                        : "bg-[var(--ps-panel)] text-[color:var(--ps-muted)]",
                    )}
                  >
                    <div className={cn(
                      "mb-1 text-[11px] font-semibold",
                      m.role === "user" ? "text-white/70" : "text-[color:var(--ps-subtle)]"
                    )}>
                      {m.role === "user" ? "You" : "PayScope AI Analyst"}
                    </div>
                    <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
                  </div>
                ))}
                {sending && (
                  <div className="max-w-[92%] rounded-xl border bg-[var(--ps-panel)] px-4 py-3">
                    <div className="mb-1 text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                      PayScope AI Analyst
                    </div>
                    <div className="flex items-center gap-2 text-sm text-[color:var(--ps-muted)]">
                      <span className="animate-pulse">●</span>
                      Analyzing reports and generating insights...
                    </div>
                  </div>
                )}
                <div ref={endRef} />
              </div>
            </div>

            <div className="mt-4 flex items-end gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedReport ? "Ask about declines, settlement volume, forecasts, comparisons…" : "Select a report to start chatting…"}
                disabled={!selectedReport || sending}
                className="min-h-[44px] flex-1 resize-none rounded-md border bg-[var(--ps-panel)] px-3 py-2 text-sm text-[color:var(--ps-fg)] outline-none focus-visible:ring-2 focus-visible:ring-[var(--ps-gold)] disabled:opacity-60"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (canSend) void send();
                  }
                }}
              />
              <Button type="button" disabled={!canSend} onClick={() => void send()}>
                {sending ? "Thinking…" : "Send"}
              </Button>
            </div>
            <div className="mt-2 text-[11px] text-[color:var(--ps-subtle)]">
              Press Enter to send · Shift+Enter for newline
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Example queries</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="w-full rounded-lg border bg-[var(--ps-panel)] px-4 py-3 text-left text-sm font-semibold text-[color:var(--ps-muted)] transition hover:bg-black/[0.03] hover:text-[color:var(--ps-fg)]"
                  onClick={() => setInput(q)}
                >
                  {q}
                </button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Query Types</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg border bg-[var(--ps-panel-2)] p-3">
                <div className="text-xs font-semibold text-[color:var(--ps-blue)]">DESCRIPTIVE</div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  "What's the approval rate?" "Show settlement summary"
                </div>
              </div>
              <div className="rounded-lg border bg-[var(--ps-panel-2)] p-3">
                <div className="text-xs font-semibold text-[color:var(--ps-gold)]">COMPARISON</div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  "Compare Visa vs Mastercard" "How does this week compare?"
                </div>
              </div>
              <div className="rounded-lg border bg-[var(--ps-panel-2)] p-3">
                <div className="text-xs font-semibold text-[color:var(--ps-good)]">FORECAST</div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  "Predict next month's volume" "What's the 30-day forecast?"
                </div>
              </div>
              <div className="rounded-lg border bg-[var(--ps-panel-2)] p-3">
                <div className="text-xs font-semibold text-[color:var(--ps-warn)]">SIMULATION</div>
                <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
                  "What if fraud increases 20%?" "Simulate 3DS2 impact"
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Architecture</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs leading-5 text-[color:var(--ps-subtle)]">
                <p className="mb-2">
                  <strong>RAG Pipeline:</strong> Questions are classified by intent, then relevant context is retrieved from vector store, graph DB, and time-series.
                </p>
                <p className="mb-2">
                  <strong>Multi-Agent:</strong> Specialized agents (Reconciliation, Fraud, Forecasting, Compliance) collaborate to generate answers.
                </p>
                <p>
                  <strong>Citations:</strong> All responses include referenced metrics and sources for explainability.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
