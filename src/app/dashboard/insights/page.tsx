"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useDashboardStore } from "@/app/dashboard/DashboardProvider";
import type { InsightsResponse } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  generateInsights,
  generateForecast,
  crossAnalysis,
  getTrends,
  isBackendAvailable,
  transformInsightsResponse,
  type ForecastResponse,
  type CrossAnalysisResponse,
  type TrendsResponse,
} from "@/lib/api";

type ApiResp = InsightsResponse;

type View = "Overview" | "Forecasting" | "Cross-Analysis";
type HeroMetric = "Transactions" | "Declines";
type ForecastMetric = "transactions" | "settlement" | "declines" | "interchange";

// Animated gradient orb component
function FloatingOrb({ className, delay = 0 }: { className?: string; delay?: number }) {
  return (
    <div 
      className={cn("absolute rounded-full blur-3xl animate-pulse", className)}
      style={{ animationDelay: `${delay}ms`, animationDuration: '4s' }}
    />
  );
}

// Sparkle icon for AI features
function SparkleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
    </svg>
  );
}

export default function InsightsPage() {
  const { selectedReportId, filters, selectedReport } = useDashboardStore();

  const [data, setData] = useState<ApiResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [view, setView] = useState<View>("Overview");
  const [heroMetric, setHeroMetric] = useState<HeroMetric>("Transactions");
  const [useBackend, setUseBackend] = useState<boolean | null>(null);

  // Forecasting state
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [forecastMetric, setForecastMetric] = useState<ForecastMetric>("transactions");
  const [forecastLoading, setForecastLoading] = useState(false);

  // Cross-analysis state
  const [crossData, setCrossData] = useState<CrossAnalysisResponse | null>(null);
  const [crossLoading, setCrossLoading] = useState(false);

  // Trends state
  const [trendsData, setTrendsData] = useState<TrendsResponse | null>(null);

  // Check if FastAPI backend is available
  useEffect(() => {
    isBackendAvailable().then(setUseBackend);
  }, []);

  // Fetch insights data
  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setErr(null);
      try {
        if (useBackend) {
          // Use FastAPI backend
          const response = await generateInsights(selectedReportId, {
            network: filters.network,
            range_days: filters.rangeDays,
          });
          if (!cancelled) {
            setData(transformInsightsResponse(response) as ApiResp);
          }
          
          // Also fetch trends
          const trends = await getTrends(selectedReportId);
          if (!cancelled) setTrendsData(trends);
        } else {
          // Fallback to Next.js API route
          const res = await fetch("/api/insights", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              reportId: selectedReportId,
              filters,
            }),
          });
          if (!res.ok) throw new Error(`Insights failed (${res.status})`);
          const json = (await res.json()) as ApiResp;
          if (!cancelled) setData(json);
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Insights error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (selectedReportId && useBackend !== null) void run();
    return () => {
      cancelled = true;
    };
  }, [selectedReportId, filters, useBackend]);

  // Fetch forecast when metric changes
  useEffect(() => {
    if (view !== "Forecasting" || !selectedReportId || !useBackend) return;
    
    let cancelled = false;
    async function fetchForecast() {
      setForecastLoading(true);
      try {
        const response = await generateForecast(selectedReportId, forecastMetric, 30);
        if (!cancelled) setForecastData(response);
      } catch (e) {
        console.error("Forecast error:", e);
      } finally {
        if (!cancelled) setForecastLoading(false);
      }
    }
    fetchForecast();
    return () => { cancelled = true; };
  }, [view, selectedReportId, forecastMetric, useBackend]);

  // Fetch cross-analysis
  useEffect(() => {
    if (view !== "Cross-Analysis" || !useBackend) return;
    
    let cancelled = false;
    async function fetchCrossAnalysis() {
      setCrossLoading(true);
      try {
        // Use first auth and settlement reports
        const response = await crossAnalysis(
          "r_auth_visa_dec",
          "r_settle_visa_dec",
          { network: filters.network, range_days: filters.rangeDays }
        );
        if (!cancelled) setCrossData(response);
      } catch (e) {
        console.error("Cross-analysis error:", e);
      } finally {
        if (!cancelled) setCrossLoading(false);
      }
    }
    fetchCrossAnalysis();
    return () => { cancelled = true; };
  }, [view, filters, useBackend]);

  const emptyState = useMemo(() => {
    if (!selectedReport) return "Select a report to view insights.";
    if (loading) return "Generating AI insights…";
    if (err) return err;
    return null;
  }, [selectedReport, loading, err]);

  const header = useMemo(() => {
    const title = selectedReport ? `${selectedReport.type} insights` : "AI Insights";
    const subtitle = selectedReport
      ? `${selectedReport.network} · Last ${filters.rangeDays} days · ${filters.network === "All" ? "All networks" : filters.network}`
      : "AI-powered analysis of payment reports";
    return { title, subtitle };
  }, [selectedReport, filters]);

  const heroSeries = useMemo(() => {
    if (!data) return [];
    if (heroMetric === "Transactions") {
      return data.charts.transactionsOverTime.map((d) => ({
        x: d.dateISO,
        v: d.count,
      }));
    }
    return data.charts.declinesByHour.map((d) => ({
      x: `${d.hour}:00`,
      v: d.declines,
    }));
  }, [data, heroMetric]);

  const heroDelta = useMemo(() => {
    if (heroSeries.length < 2) return null;
    const a = heroSeries[heroSeries.length - 2]?.v ?? 0;
    const b = heroSeries[heroSeries.length - 1]?.v ?? 0;
    if (a === 0) return null;
    const pct = ((b - a) / a) * 100;
    return { pct, up: pct >= 0 };
  }, [heroSeries]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-white to-violet-50/40 p-6 lg:p-8">
      {/* Animated background elements */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <FloatingOrb className="h-96 w-96 bg-violet-300/20 -left-48 top-20" delay={0} />
        <FloatingOrb className="h-80 w-80 bg-sky-300/20 right-10 top-40" delay={1000} />
        <FloatingOrb className="h-72 w-72 bg-emerald-300/15 left-1/3 bottom-20" delay={2000} />
        <FloatingOrb className="h-64 w-64 bg-amber-300/15 right-1/4 bottom-40" delay={1500} />
        {/* Grid pattern overlay */}
        <div 
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgb(15 23 42) 1px, transparent 0)`,
            backgroundSize: '32px 32px'
          }}
        />
      </div>

      <div className="relative grid gap-8">
        {/* Header Section */}
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/30">
                <SparkleIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                  {header.title}
                </h1>
                <p className="mt-0.5 text-sm font-medium text-slate-500">{header.subtitle}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold shadow-sm",
              useBackend 
                ? "bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-sky-500/25" 
                : "bg-slate-100 text-slate-600"
            )}>
              <span className={cn("h-1.5 w-1.5 rounded-full", useBackend ? "bg-white animate-pulse" : "bg-slate-400")} />
              {useBackend ? "FastAPI Connected" : "Mock Mode"}
            </span>
            {useBackend && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-3 py-1.5 text-xs font-bold text-white shadow-sm shadow-amber-500/25">
                <SparkleIcon className="h-3 w-3" />
                AI-Powered
              </span>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 rounded-2xl bg-white/60 p-1.5 shadow-lg shadow-slate-200/50 backdrop-blur-xl border border-slate-200/60 w-fit">
          {(["Overview", "Forecasting", "Cross-Analysis"] as const).map((t) => {
            const icons = {
              Overview: (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              ),
              Forecasting: (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              ),
              "Cross-Analysis": (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
              ),
            };
            return (
              <button
                key={t}
                type="button"
                onClick={() => setView(t)}
                className={cn(
                  "flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all duration-300",
                  view === t
                    ? "bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/30"
                    : "text-slate-600 hover:bg-white hover:text-slate-900 hover:shadow-md",
                )}
              >
                {icons[t]}
                {t}
              </button>
            );
          })}
        </div>

        {/* Empty State */}
        {emptyState && (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-slate-200/60 bg-white/70 p-16 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
            <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-slate-100 to-slate-200">
              {loading ? (
                <svg className="h-10 w-10 animate-spin text-violet-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <SparkleIcon className="h-10 w-10 text-slate-400" />
              )}
            </div>
            <p className="mt-6 text-lg font-semibold text-slate-700">{loading ? "Analyzing data..." : emptyState}</p>
            <p className="mt-2 text-sm text-slate-500">
              {loading ? "Our AI is generating insights from your reports" : "Select a report to unlock AI-powered analytics"}
            </p>
          </div>
        )}

      {/* Overview Tab */}
      {view === "Overview" && data ? (
        <>
          <div className="grid gap-8 lg:grid-cols-12">
            {/* Left KPI tiles */}
            <div className="lg:col-span-5 space-y-4">
              <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
                <KpiTile
                  title={data.kpis[0]?.label ?? "Authorization success rate"}
                  value={data.kpis[0]?.value ?? "—"}
                  note={data.kpis[0]?.delta ?? "Primary health signal"}
                  variant="emerald"
                  icon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                />
                <KpiTile
                  title={data.kpis[1]?.label ?? "Settlement volume (net)"}
                  value={data.kpis[1]?.value ?? "—"}
                  note={data.kpis[1]?.delta ?? "Net settlement volume"}
                  variant="sky"
                  icon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                />
                <KpiTile
                  title={data.kpis[2]?.label ?? "Interchange fees"}
                  value={data.kpis[2]?.value ?? "—"}
                  note={data.kpis[2]?.delta ?? "Cost trend"}
                  variant="violet"
                  icon={
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  }
                />
              </div>

              {/* AI Trend Indicators */}
              {trendsData && (
                <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                  <div className="border-b border-slate-100 bg-gradient-to-r from-amber-50 to-orange-50/50 px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30">
                        <SparkleIcon className="h-3.5 w-3.5 text-white" />
                      </div>
                      <span className="text-sm font-bold text-slate-800">AI-Detected Trends</span>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(trendsData.trends).map(([key, trend]) => (
                        <div 
                          key={key} 
                          className={cn(
                            "relative overflow-hidden rounded-2xl border p-3 transition-all duration-300 hover:scale-[1.02]",
                            trend.direction === "up" 
                              ? "border-emerald-200 bg-gradient-to-br from-emerald-50 to-teal-50/50" 
                              : trend.direction === "down" 
                                ? "border-rose-200 bg-gradient-to-br from-rose-50 to-pink-50/50"
                                : "border-slate-200 bg-slate-50"
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-xl text-lg font-bold",
                              trend.direction === "up" 
                                ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30" 
                                : trend.direction === "down" 
                                  ? "bg-rose-500 text-white shadow-lg shadow-rose-500/30"
                                  : "bg-slate-400 text-white"
                            )}>
                              {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"}
                            </span>
                            <div>
                              <div className="text-xs font-bold text-slate-800 capitalize">{key}</div>
                              <div className={cn(
                                "text-xs font-semibold",
                                trend.change_percent > 0 ? "text-emerald-600" : trend.change_percent < 0 ? "text-rose-600" : "text-slate-500"
                              )}>
                                {trend.change_percent > 0 ? "+" : ""}{trend.change_percent}%
                              </div>
                            </div>
                          </div>
                          {trend.anomaly_detected && (
                            <span className="absolute right-2 top-2 rounded-full bg-amber-400 px-2 py-0.5 text-[9px] font-bold text-white shadow-lg shadow-amber-500/30">
                              ANOMALY
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right hero chart panel */}
            <div className="lg:col-span-7">
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 shadow-2xl shadow-slate-900/50">
                {/* Decorative elements */}
                <div className="absolute inset-0 overflow-hidden">
                  <div className="absolute -right-20 -top-20 h-60 w-60 rounded-full bg-violet-500/20 blur-3xl" />
                  <div className="absolute -left-20 bottom-0 h-40 w-40 rounded-full bg-sky-500/20 blur-3xl" />
                </div>
                
                <div className="relative">
                  <div className="flex flex-wrap items-start justify-between gap-4 px-6 pt-6">
                    <div>
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm">
                          {heroMetric === "Transactions" ? (
                            <svg className="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                          ) : (
                            <svg className="h-4 w-4 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                            </svg>
                          )}
                        </div>
                        <span className="text-xs font-semibold uppercase tracking-widest text-white/60">
                          {heroMetric === "Transactions" ? "Transactions over time" : "Declines by hour"}
                        </span>
                      </div>
                      <div className="mt-4 flex items-end gap-4">
                        <div className="font-mono text-6xl font-bold leading-none tracking-tight text-white">
                          {heroSeries[heroSeries.length - 1]?.v ?? "—"}
                        </div>
                        {heroDelta && (
                          <div className={cn(
                            "mb-2 flex items-center gap-1 rounded-full px-3 py-1 text-sm font-bold",
                            heroDelta.up 
                              ? "bg-emerald-500/20 text-emerald-400" 
                              : "bg-rose-500/20 text-rose-400"
                          )}>
                            {heroDelta.up ? "↑" : "↓"} {heroDelta.up ? "+" : ""}{heroDelta.pct.toFixed(0)}%
                          </div>
                        )}
                      </div>
                      <div className="mt-2 text-sm text-white/50">
                        {heroMetric === "Transactions" ? "Latest bucket count" : "Authorization declines"}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 rounded-xl bg-white/5 p-1 backdrop-blur-sm">
                      <button
                        type="button"
                        onClick={() => setHeroMetric("Transactions")}
                        className={cn(
                          "rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-300",
                          heroMetric === "Transactions"
                            ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/30"
                            : "text-white/60 hover:bg-white/10 hover:text-white",
                        )}
                      >
                        Transactions
                      </button>
                      <button
                        type="button"
                        onClick={() => setHeroMetric("Declines")}
                        className={cn(
                          "rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-300",
                          heroMetric === "Declines"
                            ? "bg-gradient-to-r from-rose-400 to-pink-500 text-white shadow-lg shadow-rose-500/30"
                            : "text-white/60 hover:bg-white/10 hover:text-white",
                        )}
                      >
                        Declines
                      </button>
                    </div>
                  </div>

                  <div className="h-[260px] px-3 pt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={heroSeries}>
                        <defs>
                          <linearGradient id="heroGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={heroMetric === "Transactions" ? "#f59e0b" : "#f43f5e"} stopOpacity={0.4} />
                            <stop offset="100%" stopColor={heroMetric === "Transactions" ? "#f59e0b" : "#f43f5e"} stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="x" stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
                        <YAxis stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
                        <Tooltip
                          contentStyle={{
                            background: "rgba(15,23,42,0.95)",
                            border: "1px solid rgba(255,255,255,0.1)",
                            borderRadius: 16,
                            color: "#fff",
                            boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="v"
                          stroke={heroMetric === "Transactions" ? "#f59e0b" : "#f43f5e"}
                          strokeWidth={3}
                          fill="url(#heroGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="grid gap-px border-t border-white/10 bg-white/5 sm:grid-cols-3">
                    <MiniHeroStat label={data.kpis[0]?.label ?? "Auth success rate"} value={data.kpis[0]?.value ?? "—"} color="emerald" />
                    <MiniHeroStat label={data.kpis[1]?.label ?? "Net settlement"} value={data.kpis[1]?.value ?? "—"} color="sky" />
                    <MiniHeroStat label={data.kpis[2]?.label ?? "Interchange"} value={data.kpis[2]?.value ?? "—"} color="violet" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Insight Cards & Charts Row */}
          <div className="grid gap-8 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/30">
                  <SparkleIcon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-slate-900">AI-Generated Insights</h2>
                  <p className="text-sm text-slate-500">Intelligent analysis of your payment data</p>
                </div>
              </div>
              <div className="space-y-4">
                {data.insightCards.map((c, idx) => (
                  <div 
                    key={c.id} 
                    className="group relative overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 p-5 shadow-xl shadow-slate-200/50 backdrop-blur-xl transition-all duration-500 hover:shadow-2xl hover:shadow-slate-300/50"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-transparent to-violet-50/30 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                    <div className="relative">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className={cn(
                              "flex h-6 w-6 items-center justify-center rounded-lg",
                              c.severity === "risk" 
                                ? "bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30"
                                : c.severity === "watch"
                                  ? "bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg shadow-sky-500/30"
                                  : "bg-gradient-to-br from-slate-400 to-slate-500 shadow-lg shadow-slate-500/20"
                            )}>
                              {c.severity === "risk" ? (
                                <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                              ) : (
                                <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                            </span>
                            <h3 className="text-sm font-bold text-slate-900">{c.title}</h3>
                          </div>
                          <p className="mt-2 text-sm leading-relaxed text-slate-600">{c.narrative}</p>
                        </div>
                        <span className={cn(
                          "shrink-0 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider",
                          c.severity === "risk" 
                            ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/25"
                            : c.severity === "watch"
                              ? "bg-gradient-to-r from-sky-400 to-blue-500 text-white shadow-lg shadow-sky-500/25"
                              : "bg-slate-100 text-slate-600"
                        )}>
                          {c.severity}
                        </span>
                      </div>
                      <div className="mt-4 grid gap-3 sm:grid-cols-3">
                        {c.supportingMetrics.map((m) => (
                          <div key={m.label} className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-slate-50 to-white p-3 transition-all duration-300 hover:border-violet-200 hover:shadow-md">
                            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{m.label}</div>
                            <div className="mt-1 font-mono text-lg font-bold text-slate-900">{m.value}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 shadow-lg shadow-rose-500/30">
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-slate-900">Decline Distribution</h2>
                  <p className="text-sm text-slate-500">Hourly authorization analysis</p>
                </div>
              </div>
              <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 p-5 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                <div className="h-[320px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.charts.declinesByHour}>
                      <defs>
                        <linearGradient id="declineGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#f43f5e" stopOpacity={1} />
                          <stop offset="100%" stopColor="#ec4899" stopOpacity={0.8} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
                      <XAxis 
                        dataKey="hour" 
                        stroke="#94a3b8" 
                        fontSize={11} 
                        tickLine={false} 
                        axisLine={false}
                        tickFormatter={(v) => `${v}h`}
                      />
                      <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(255,255,255,0.98)",
                          border: "1px solid rgba(148,163,184,0.2)",
                          borderRadius: 16,
                          boxShadow: "0 20px 40px rgba(0,0,0,0.1)",
                        }}
                        cursor={{ fill: 'rgba(244,63,94,0.05)' }}
                      />
                      <Bar 
                        dataKey="declines" 
                        fill="url(#declineGradient)" 
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}

      {/* Forecasting Tab */}
      {view === "Forecasting" && (
        <div className="grid gap-8">
          {/* Metric Selector */}
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-sm font-semibold text-slate-600">Forecast metric:</span>
            <div className="flex items-center gap-1 rounded-2xl bg-white/60 p-1.5 shadow-lg shadow-slate-200/50 backdrop-blur-xl border border-slate-200/60">
              {(["transactions", "settlement", "declines", "interchange"] as const).map((m) => {
                const icons = {
                  transactions: <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>,
                  settlement: <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
                  declines: <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>,
                  interchange: <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>,
                };
                const colors = {
                  transactions: "from-emerald-500 to-teal-600 shadow-emerald-500/30",
                  settlement: "from-sky-500 to-blue-600 shadow-sky-500/30",
                  declines: "from-rose-500 to-pink-600 shadow-rose-500/30",
                  interchange: "from-violet-500 to-purple-600 shadow-violet-500/30",
                };
                return (
                  <button
                    key={m}
                    onClick={() => setForecastMetric(m)}
                    className={cn(
                      "flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold capitalize transition-all duration-300",
                      forecastMetric === m
                        ? `bg-gradient-to-r ${colors[m]} text-white shadow-lg`
                        : "text-slate-600 hover:bg-white hover:text-slate-900 hover:shadow-md"
                    )}
                  >
                    {icons[m]}
                    {m}
                  </button>
                );
              })}
            </div>
          </div>

          {forecastLoading ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-slate-200/60 bg-white/70 p-16 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-100 to-purple-100">
                <svg className="h-8 w-8 animate-spin text-violet-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
              <p className="mt-6 text-lg font-semibold text-slate-700">Generating AI Forecast</p>
              <p className="mt-2 text-sm text-slate-500">Training predictive models on your data...</p>
            </div>
          ) : !useBackend ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-amber-200/60 bg-gradient-to-br from-amber-50 to-orange-50/50 p-16 shadow-xl shadow-amber-200/30">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="mt-6 text-lg font-bold text-slate-800">Backend Required</p>
              <p className="mt-2 text-center text-sm text-slate-600">Start the FastAPI backend server to enable AI-powered forecasting</p>
            </div>
          ) : forecastData ? (
            <div className="grid gap-8 lg:grid-cols-12">
              <div className="lg:col-span-8">
                <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                  <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 shadow-lg shadow-sky-500/30">
                          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-slate-900 capitalize">{forecastData.metric} Forecast</h3>
                          <p className="text-sm text-slate-500">{forecastData.horizon_days}-day prediction with confidence intervals</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold shadow-sm",
                          forecastData.trend === "up" 
                            ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-emerald-500/25"
                            : forecastData.trend === "down"
                              ? "bg-gradient-to-r from-rose-500 to-pink-500 text-white shadow-rose-500/25"
                              : "bg-slate-100 text-slate-600"
                        )}>
                          {forecastData.trend === "up" ? "↑ Trending Up" : forecastData.trend === "down" ? "↓ Trending Down" : "→ Stable"}
                        </span>
                        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600">
                          {(forecastData.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="h-[320px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={forecastData.forecast}>
                          <defs>
                            <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.3} />
                              <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.1} />
                              <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.05} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid stroke="rgba(148,163,184,0.1)" vertical={false} />
                          <XAxis dataKey="date_iso" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                          <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                          <Tooltip
                            contentStyle={{
                              background: "rgba(255,255,255,0.98)",
                              border: "1px solid rgba(148,163,184,0.2)",
                              borderRadius: 16,
                              boxShadow: "0 20px 40px rgba(0,0,0,0.1)",
                            }}
                          />
                          <Area type="monotone" dataKey="upper_bound" stroke="none" fill="url(#confidenceGradient)" />
                          <Area type="monotone" dataKey="lower_bound" stroke="none" fill="rgba(255,255,255,1)" />
                          <Area type="monotone" dataKey="predicted" stroke="#0ea5e9" strokeWidth={3} fill="url(#forecastGradient)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="lg:col-span-4 space-y-6">
                <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                  <div className="border-b border-slate-100 bg-gradient-to-r from-violet-50 to-purple-50/50 px-5 py-3">
                    <div className="flex items-center gap-2">
                      <SparkleIcon className="h-4 w-4 text-violet-500" />
                      <span className="text-sm font-bold text-slate-800">AI Analysis</span>
                    </div>
                  </div>
                  <div className="p-5">
                    <p className="text-sm leading-relaxed text-slate-600">{forecastData.narrative}</p>
                  </div>
                </div>

                <div className="grid gap-4">
                  <div className="group relative overflow-hidden rounded-2xl border border-emerald-200/60 bg-gradient-to-br from-emerald-50 to-teal-50/50 p-4 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-600">Trend Direction</div>
                    <div className="mt-2 text-2xl font-bold text-slate-900 capitalize">{forecastData.trend}</div>
                    <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-emerald-500/10 blur-2xl transition-all duration-300 group-hover:bg-emerald-500/20" />
                  </div>
                  <div className="group relative overflow-hidden rounded-2xl border border-sky-200/60 bg-gradient-to-br from-sky-50 to-blue-50/50 p-4 transition-all duration-300 hover:shadow-lg hover:shadow-sky-500/10">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-sky-600">Model Confidence</div>
                    <div className="mt-2 font-mono text-2xl font-bold text-slate-900">{(forecastData.confidence * 100).toFixed(0)}%</div>
                    <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-sky-500/10 blur-2xl transition-all duration-300 group-hover:bg-sky-500/20" />
                  </div>
                  <div className="group relative overflow-hidden rounded-2xl border border-violet-200/60 bg-gradient-to-br from-violet-50 to-purple-50/50 p-4 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-violet-600">Forecast Horizon</div>
                    <div className="mt-2 text-2xl font-bold text-slate-900">{forecastData.horizon_days} <span className="text-lg font-medium text-slate-500">days</span></div>
                    <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-violet-500/10 blur-2xl transition-all duration-300 group-hover:bg-violet-500/20" />
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Cross-Analysis Tab */}
      {view === "Cross-Analysis" && (
        <div className="grid gap-8">
          {crossLoading ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-slate-200/60 bg-white/70 p-16 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
              <div className="relative">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-100 to-blue-100">
                  <svg className="h-8 w-8 animate-spin text-sky-500" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
                <div className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30">
                  <SparkleIcon className="h-3 w-3 text-white" />
                </div>
              </div>
              <p className="mt-6 text-lg font-semibold text-slate-700">Running Cross-Analysis</p>
              <p className="mt-2 text-sm text-slate-500">Comparing authorization and settlement data...</p>
            </div>
          ) : !useBackend ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-amber-200/60 bg-gradient-to-br from-amber-50 to-orange-50/50 p-16 shadow-xl shadow-amber-200/30">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="mt-6 text-lg font-bold text-slate-800">Backend Required</p>
              <p className="mt-2 text-center text-sm text-slate-600">Start the FastAPI backend to enable auth vs settlement comparison</p>
            </div>
          ) : crossData ? (
            <>
              {/* Main Reconciliation Table */}
              <div className="overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 shadow-xl shadow-slate-200/50 backdrop-blur-xl">
                <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 shadow-lg shadow-sky-500/30">
                        <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-slate-900">Authorization vs Settlement</h3>
                        <p className="text-sm text-slate-500">Cross-report reconciliation analysis</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-2 text-sm font-bold text-white shadow-lg shadow-emerald-500/25">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {crossData.reconciliation_rate.toFixed(1)}% Reconciled
                    </span>
                  </div>
                </div>

                <div className="p-6">
                  <div className="overflow-hidden rounded-2xl border border-slate-200/80">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gradient-to-r from-slate-50 to-slate-100/50">
                          <th className="px-5 py-4 text-left text-[11px] font-bold uppercase tracking-wider text-slate-500">Metric</th>
                          <th className="px-5 py-4 text-right text-[11px] font-bold uppercase tracking-wider text-slate-500">Authorization</th>
                          <th className="px-5 py-4 text-right text-[11px] font-bold uppercase tracking-wider text-slate-500">Settlement</th>
                          <th className="px-5 py-4 text-right text-[11px] font-bold uppercase tracking-wider text-slate-500">Variance</th>
                          <th className="px-5 py-4 text-center text-[11px] font-bold uppercase tracking-wider text-slate-500">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {crossData.metrics.map((m, idx) => (
                          <tr key={m.label} className={cn("transition-colors duration-150 hover:bg-sky-50/50", idx % 2 === 0 ? "bg-white" : "bg-slate-50/30")}>
                            <td className="px-5 py-4 text-sm font-semibold text-slate-800">{m.label}</td>
                            <td className="px-5 py-4 text-right font-mono text-sm text-slate-600">{m.auth_value}</td>
                            <td className="px-5 py-4 text-right font-mono text-sm text-slate-600">{m.settlement_value}</td>
                            <td className="px-5 py-4 text-right font-mono text-sm font-medium text-slate-800">{m.variance}</td>
                            <td className="px-5 py-4 text-center">
                              <span className={cn(
                                "inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-wider",
                                m.status === "aligned" 
                                  ? "bg-emerald-100 text-emerald-700"
                                  : m.status === "watch"
                                    ? "bg-amber-100 text-amber-700"
                                    : "bg-rose-100 text-rose-700"
                              )}>
                                {m.status === "aligned" && <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                                {m.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* AI Analysis Summary */}
              <div className="overflow-hidden rounded-3xl border border-violet-200/60 bg-gradient-to-br from-violet-50/80 to-purple-50/40 shadow-xl shadow-violet-200/30 backdrop-blur-xl">
                <div className="border-b border-violet-100/60 bg-gradient-to-r from-violet-100/50 to-purple-100/30 px-6 py-4">
                  <div className="flex items-center gap-2">
                    <SparkleIcon className="h-5 w-5 text-violet-500" />
                    <h3 className="text-lg font-bold text-slate-900">AI Analysis Summary</h3>
                  </div>
                </div>
                <div className="p-6">
                  <p className="text-sm leading-relaxed text-slate-700">{crossData.narrative}</p>
                </div>
              </div>

              {/* Insight Cards */}
              <div className="grid gap-6 md:grid-cols-2">
                {crossData.insights.map((insight, idx) => (
                  <div 
                    key={insight.id} 
                    className="group relative overflow-hidden rounded-3xl border border-slate-200/60 bg-white/80 p-5 shadow-xl shadow-slate-200/50 backdrop-blur-xl transition-all duration-500 hover:shadow-2xl"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-transparent to-sky-50/30 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                    <div className="relative">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "flex h-8 w-8 items-center justify-center rounded-xl",
                            insight.severity === "risk" 
                              ? "bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-amber-500/30"
                              : "bg-gradient-to-br from-sky-400 to-blue-500 shadow-lg shadow-sky-500/30"
                          )}>
                            {insight.severity === "risk" ? (
                              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                              </svg>
                            ) : (
                              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            )}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900">{insight.title}</h4>
                        </div>
                        <span className={cn(
                          "shrink-0 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider",
                          insight.severity === "risk" 
                            ? "bg-gradient-to-r from-amber-400 to-orange-500 text-white shadow-lg shadow-amber-500/25"
                            : "bg-slate-100 text-slate-600"
                        )}>
                          {insight.severity}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-relaxed text-slate-600">{insight.narrative}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>
      )}
      </div>
    </div>
  );
}

function KpiTile({
  title,
  value,
  note,
  variant,
  icon,
}: {
  title: string;
  value: string;
  note: string;
  variant: "emerald" | "sky" | "violet";
  icon?: React.ReactNode;
}) {
  const styles = {
    emerald: {
      card: "border-emerald-200/60 bg-gradient-to-br from-emerald-50/80 to-teal-50/40",
      icon: "from-emerald-500 to-teal-600 shadow-emerald-500/30",
      value: "text-emerald-700",
      note: "text-emerald-600/70",
      glow: "bg-emerald-400/20",
    },
    sky: {
      card: "border-sky-200/60 bg-gradient-to-br from-sky-50/80 to-blue-50/40",
      icon: "from-sky-500 to-blue-600 shadow-sky-500/30",
      value: "text-sky-700",
      note: "text-sky-600/70",
      glow: "bg-sky-400/20",
    },
    violet: {
      card: "border-violet-200/60 bg-gradient-to-br from-violet-50/80 to-purple-50/40",
      icon: "from-violet-500 to-purple-600 shadow-violet-500/30",
      value: "text-violet-700",
      note: "text-violet-600/70",
      glow: "bg-violet-400/20",
    },
  };

  const s = styles[variant];

  return (
    <div className={cn(
      "group relative overflow-hidden rounded-3xl border p-5 shadow-xl backdrop-blur-xl transition-all duration-500 hover:scale-[1.02] hover:shadow-2xl",
      s.card
    )}>
      {/* Decorative glow */}
      <div className={cn("absolute -right-8 -top-8 h-24 w-24 rounded-full blur-3xl transition-all duration-500 group-hover:scale-150", s.glow)} />
      
      <div className="relative">
        <div className="flex items-center gap-3">
          {icon && (
            <div className={cn("flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-lg", s.icon)}>
              {icon}
            </div>
          )}
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">{title}</div>
        </div>
        <div className={cn("mt-4 font-mono text-4xl font-bold tracking-tight", s.value)}>{value}</div>
        <div className={cn("mt-2 flex items-center gap-1 text-xs font-semibold", s.note)}>
          <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          {note}
        </div>
      </div>
    </div>
  );
}

function MiniHeroStat({ label, value, color }: { label: string; value: string; color?: "emerald" | "sky" | "violet" }) {
  const dotColors = {
    emerald: "bg-emerald-400",
    sky: "bg-sky-400",
    violet: "bg-violet-400",
  };
  
  return (
    <div className="px-6 py-5 transition-colors duration-300 hover:bg-white/5">
      <div className="flex items-center gap-2">
        {color && <span className={cn("h-2 w-2 rounded-full", dotColors[color])} />}
        <div className="text-[11px] font-semibold uppercase tracking-wider text-white/50">{label}</div>
      </div>
      <div className="mt-2 font-mono text-xl font-bold text-white">{value}</div>
    </div>
  );
}
