"use client";

import { useMemo, useRef, useState } from "react";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ChatResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

type Msg = { role: "user" | "assistant"; content: string };

const EXAMPLES = [
  "Why did settlement amounts drop last week?",
  "Compare Visa vs Mastercard approval rates",
  "Which merchants have the highest chargebacks?",
] as const;

export default function ChatPage() {
  const { selectedReportId, filters, selectedReport } = useDashboardStore();
  const [thread, setThread] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "I can analyze the selected report and explain trends like an internal payments analyst. Ask me about declines, settlement volume, interchange fees, or network comparisons.",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

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

      const appendix =
        data.metricsUsed.length === 0
          ? ""
          : `\n\nMetrics referenced:\n${data.metricsUsed
              .map((m) => `- ${m.label}: ${m.value}`)
              .join("\n")}`;

      const followups =
        data.followups.length === 0
          ? ""
          : `\n\nSuggested follow-ups:\n${data.followups.map((f) => `- ${f}`).join("\n")}`;

      setThread((prev) => [
        ...prev,
        { role: "assistant", content: `${data.answer}${appendix}${followups}` },
      ]);
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ behavior: "smooth" }));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Chat error");
      setThread((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn’t generate a response. Try again or switch to a different report.",
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
          <div className="text-sm font-semibold text-[color:var(--ps-fg)]">AI Chat</div>
          <div className="mt-1 text-xs text-[color:var(--ps-subtle)]">
            ChatGPT-style UI. Deterministic responses via structured `/api/chat` (AI-ready).
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone="blue">/api/chat</Badge>
          <Badge>{reportHint}</Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        <Card className="lg:col-span-8">
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Conversation</CardTitle>
            {err ? (
              <div className="text-xs font-semibold text-[var(--ps-bad)]">{err}</div>
            ) : null}
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
                        ? "ml-auto bg-[var(--ps-panel)] text-[color:var(--ps-fg)]"
                        : "bg-[var(--ps-panel)] text-[color:var(--ps-muted)]",
                    )}
                  >
                    <div className="mb-1 text-[11px] font-semibold text-[color:var(--ps-subtle)]">
                      {m.role === "user" ? "You" : "PayScope Analyst"}
                    </div>
                    <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
                  </div>
                ))}
                <div ref={endRef} />
              </div>
            </div>

            <div className="mt-4 flex items-end gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedReport ? "Ask about declines, settlement volume, interchange…" : "Select a report to start chatting…"}
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

        <Card className="lg:col-span-4">
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

            <div className="mt-4 rounded-lg border bg-[var(--ps-panel)] p-4">
              <div className="text-xs font-semibold text-[color:var(--ps-subtle)]">AI-ready note</div>
              <div className="mt-1 text-xs leading-5 text-[color:var(--ps-subtle)]">
                Requests are structured to support future RAG (report embeddings + citations). For demo, responses are deterministic and reference computed metrics.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}


