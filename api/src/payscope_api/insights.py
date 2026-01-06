"""
Insights, Forecasting, and Intelligence API endpoints.

Features:
1. AI-generated insights from payment reports
2. Trends and forecasts based on report content
3. Cross-analysis across different reports (authorization vs settlement)
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/insights", tags=["insights"])


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class ReportFilters(BaseModel):
    network: Literal["All", "Visa", "Mastercard"] = "All"
    range_days: int = 7


class InsightsRequest(BaseModel):
    report_id: str
    filters: ReportFilters


class Kpi(BaseModel):
    label: str
    value: str
    delta: Optional[str] = None
    tone: Literal["neutral", "good", "warn", "bad"] = "neutral"


class SupportingMetric(BaseModel):
    label: str
    value: str


class InsightCard(BaseModel):
    id: str
    title: str
    narrative: str
    supporting_metrics: list[SupportingMetric]
    severity: Literal["info", "watch", "risk"]


class ChartDataPoint(BaseModel):
    label: str
    value: float


class TransactionTimeSeries(BaseModel):
    date_iso: str
    count: int


class DeclinesByHour(BaseModel):
    hour: int
    declines: int


class NetworkComparison(BaseModel):
    label: str
    visa: float
    mastercard: float


class ChartsData(BaseModel):
    transactions_over_time: list[TransactionTimeSeries]
    declines_by_hour: list[DeclinesByHour]
    network_comparison: list[NetworkComparison]


class InsightsResponse(BaseModel):
    kpis: list[Kpi]
    charts: ChartsData
    insight_cards: list[InsightCard]


class ForecastRequest(BaseModel):
    report_id: str
    metric: Literal["transactions", "settlement", "declines", "interchange"]
    horizon_days: int = 30


class ForecastPoint(BaseModel):
    date_iso: str
    predicted: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    metric: str
    horizon_days: int
    forecast: list[ForecastPoint]
    trend: Literal["up", "down", "stable"]
    confidence: float
    narrative: str


class CrossAnalysisRequest(BaseModel):
    auth_report_id: str
    settlement_report_id: str
    filters: ReportFilters


class CrossAnalysisMetric(BaseModel):
    label: str
    auth_value: str
    settlement_value: str
    variance: str
    status: Literal["aligned", "watch", "mismatch"]


class CrossAnalysisResponse(BaseModel):
    auth_report_id: str
    settlement_report_id: str
    metrics: list[CrossAnalysisMetric]
    insights: list[InsightCard]
    reconciliation_rate: float
    narrative: str


# --------------------------------------------------------------------------
# Mock Data Generation (deterministic for demo)
# --------------------------------------------------------------------------

def _seed_random(seed: str) -> None:
    """Seed random for deterministic outputs."""
    random.seed(hash(seed) % (2**32))


def _generate_transactions_over_time(days: int = 7) -> list[TransactionTimeSeries]:
    """Generate mock transaction time series."""
    base_date = datetime.now() - timedelta(days=days)
    data = []
    for i in range(days):
        date = base_date + timedelta(days=i)
        # Simulate weekend dips
        is_weekend = date.weekday() >= 5
        base_count = 15000 if is_weekend else 22000
        variance = random.randint(-2000, 3000)
        data.append(TransactionTimeSeries(
            date_iso=date.strftime("%Y-%m-%d"),
            count=base_count + variance
        ))
    return data


def _generate_declines_by_hour() -> list[DeclinesByHour]:
    """Generate mock declines by hour with late-night spike pattern."""
    data = []
    for hour in range(24):
        # Late-night spike pattern (10 PM - 2 AM)
        if 22 <= hour or hour <= 2:
            base_declines = random.randint(80, 120)
        else:
            base_declines = random.randint(30, 60)
        data.append(DeclinesByHour(hour=hour, declines=base_declines))
    return data


def _generate_network_comparison() -> list[NetworkComparison]:
    """Generate Visa vs Mastercard comparison metrics."""
    return [
        NetworkComparison(label="Transaction Volume", visa=58.4, mastercard=41.6),
        NetworkComparison(label="Approval Rate", visa=92.1, mastercard=91.8),
        NetworkComparison(label="Avg Transaction", visa=47.50, mastercard=52.30),
        NetworkComparison(label="Cross-border %", visa=12.3, mastercard=15.7),
    ]


# --------------------------------------------------------------------------
# API Endpoints
# --------------------------------------------------------------------------

@router.post("/generate", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest) -> InsightsResponse:
    """
    Generate AI-powered insights from payment reports.
    
    Uses GenAI/RAG to:
    - Extract key metrics and KPIs
    - Identify trends and anomalies
    - Generate natural language insights
    """
    _seed_random(request.report_id)
    
    # Generate mock KPIs
    approval_rate = round(random.uniform(90.5, 93.5), 1)
    settlement_volume = round(random.uniform(1.8, 2.2), 2)
    interchange_fees = round(random.uniform(32, 38), 1)
    
    late_decline_lift = round(random.uniform(15, 35), 0)
    
    kpis = [
        Kpi(
            label="Authorization success rate",
            value=f"{approval_rate}%",
            delta=f"Late-night declines elevated (+{late_decline_lift}% vs daytime)",
            tone="warn" if late_decline_lift > 25 else "neutral"
        ),
        Kpi(
            label="Settlement volume (net)",
            value=f"${settlement_volume}M",
            delta="Avg settlement delay: 1.2 days",
            tone="neutral"
        ),
        Kpi(
            label="Interchange fees",
            value=f"${interchange_fees}K",
            delta="Trending upward +3.2%",
            tone="warn"
        ),
    ]
    
    # Generate charts data
    charts = ChartsData(
        transactions_over_time=_generate_transactions_over_time(request.filters.range_days),
        declines_by_hour=_generate_declines_by_hour(),
        network_comparison=_generate_network_comparison()
    )
    
    # Generate insight cards
    insight_cards = [
        InsightCard(
            id="ic_declines_10pm",
            title=f"Authorization declines increased {int(late_decline_lift)}% after 10 PM",
            narrative=(
                f"Declines cluster in the late-night window (22:00–23:59 UTC). "
                f"On a per-hour basis, late-night declines run ~{int(late_decline_lift)}% higher than daytime. "
                "Primary decline codes: 91 (Issuer unavailable), 05 (Do not honor)."
            ),
            supporting_metrics=[
                SupportingMetric(label="Approval rate", value=f"{approval_rate}%"),
                SupportingMetric(label="Late-night declines", value=f"{random.randint(180, 250)}"),
                SupportingMetric(label="Total transactions", value=f"{random.randint(18000, 22000):,}"),
            ],
            severity="watch" if late_decline_lift > 25 else "info"
        ),
        InsightCard(
            id="ic_settlement_delay",
            title="Settlement delays correlate with cross-border transactions",
            narrative=(
                "Cross-border batches show longer settlement delay than domestic. "
                "Average delay is 1.8d (cross-border) vs 0.4d (domestic). "
                "Consider reviewing clearing house routing for GB/DE merchants."
            ),
            supporting_metrics=[
                SupportingMetric(label="Cross-border share", value="14.2%"),
                SupportingMetric(label="Delay delta", value="1.4 days"),
                SupportingMetric(label="Net settlement", value=f"${settlement_volume}M"),
            ],
            severity="watch"
        ),
        InsightCard(
            id="ic_interchange_trend",
            title="Interchange fees trending upward month-over-month",
            narrative=(
                "Within the current period, interchange fees increased in the latter half. "
                "This correlates with higher cross-border mix and card-not-present transactions. "
                "Recommend reviewing merchant category codes for optimization opportunities."
            ),
            supporting_metrics=[
                SupportingMetric(label="Interchange fees", value=f"${interchange_fees}K"),
                SupportingMetric(label="Period lift", value="+3.2%"),
                SupportingMetric(label="CNP share", value="28.4%"),
            ],
            severity="info"
        ),
    ]
    
    return InsightsResponse(
        kpis=kpis,
        charts=charts,
        insight_cards=insight_cards
    )


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Generate AI-powered forecasts based on historical report data.
    
    Uses time-series analysis and ML models to:
    - Predict future values for key metrics
    - Provide confidence intervals
    - Identify trend direction
    """
    _seed_random(f"{request.report_id}_{request.metric}")
    
    base_date = datetime.now()
    forecast_points = []
    
    # Generate forecast based on metric type
    if request.metric == "transactions":
        base_value = 20000
        trend_factor = 1.02  # 2% growth
        volatility = 0.08
    elif request.metric == "settlement":
        base_value = 1900000
        trend_factor = 1.015
        volatility = 0.05
    elif request.metric == "declines":
        base_value = 1200
        trend_factor = 0.98  # Declining (improvement)
        volatility = 0.12
    else:  # interchange
        base_value = 35000
        trend_factor = 1.025
        volatility = 0.06
    
    for i in range(request.horizon_days):
        date = base_date + timedelta(days=i + 1)
        predicted = base_value * (trend_factor ** i) * (1 + random.uniform(-0.02, 0.02))
        margin = predicted * volatility * (1 + i * 0.01)  # Wider margins for further dates
        
        forecast_points.append(ForecastPoint(
            date_iso=date.strftime("%Y-%m-%d"),
            predicted=round(predicted, 2),
            lower_bound=round(predicted - margin, 2),
            upper_bound=round(predicted + margin, 2)
        ))
    
    # Determine trend
    if trend_factor > 1.01:
        trend = "up"
    elif trend_factor < 0.99:
        trend = "down"
    else:
        trend = "stable"
    
    # Generate narrative
    metric_labels = {
        "transactions": "daily transaction volume",
        "settlement": "net settlement amount",
        "declines": "authorization declines",
        "interchange": "interchange fees"
    }
    
    trend_desc = {
        "up": "increase",
        "down": "decrease",
        "stable": "remain stable"
    }
    
    confidence = round(random.uniform(0.82, 0.94), 2)
    
    narrative = (
        f"Based on historical patterns and current trends, {metric_labels[request.metric]} "
        f"is forecast to {trend_desc[trend]} over the next {request.horizon_days} days. "
        f"The model shows {confidence*100:.0f}% confidence in this prediction. "
        f"Key factors: seasonal patterns, network mix, and merchant category distribution."
    )
    
    return ForecastResponse(
        metric=request.metric,
        horizon_days=request.horizon_days,
        forecast=forecast_points,
        trend=trend,
        confidence=confidence,
        narrative=narrative
    )


@router.post("/cross-analysis", response_model=CrossAnalysisResponse)
async def cross_analysis(request: CrossAnalysisRequest) -> CrossAnalysisResponse:
    """
    Perform cross-analysis between authorization and settlement reports.
    
    Enables:
    - Reconciliation between auth and settlement
    - Variance analysis
    - Identification of discrepancies
    """
    _seed_random(f"{request.auth_report_id}_{request.settlement_report_id}")
    
    # Generate cross-analysis metrics
    auth_tx_count = random.randint(18000, 22000)
    settle_tx_count = auth_tx_count - random.randint(50, 200)  # Some pending
    
    auth_volume = round(random.uniform(2.1, 2.4), 2)
    settle_volume = round(auth_volume * random.uniform(0.96, 0.99), 2)
    
    auth_approval = round(random.uniform(91, 93), 1)
    settle_success = round(random.uniform(98, 99.5), 1)
    
    recon_rate = round((settle_tx_count / auth_tx_count) * 100, 2)
    
    metrics = [
        CrossAnalysisMetric(
            label="Transaction Count",
            auth_value=f"{auth_tx_count:,}",
            settlement_value=f"{settle_tx_count:,}",
            variance=f"{auth_tx_count - settle_tx_count:,} pending",
            status="aligned" if (auth_tx_count - settle_tx_count) < 100 else "watch"
        ),
        CrossAnalysisMetric(
            label="Gross Volume",
            auth_value=f"${auth_volume}M",
            settlement_value=f"${settle_volume}M",
            variance=f"${round((auth_volume - settle_volume) * 1000, 1)}K diff",
            status="aligned" if (auth_volume - settle_volume) < 0.05 else "watch"
        ),
        CrossAnalysisMetric(
            label="Success Rate",
            auth_value=f"{auth_approval}%",
            settlement_value=f"{settle_success}%",
            variance=f"+{round(settle_success - auth_approval, 1)}% settled",
            status="aligned"
        ),
        CrossAnalysisMetric(
            label="Interchange Fees",
            auth_value="N/A",
            settlement_value=f"${round(settle_volume * 0.018 * 1000, 1)}K",
            variance="Settlement only",
            status="aligned"
        ),
        CrossAnalysisMetric(
            label="Chargeback Rate",
            auth_value=f"{round(random.uniform(0.3, 0.6), 2)}%",
            settlement_value=f"{round(random.uniform(0.25, 0.5), 2)}%",
            variance="Within threshold",
            status="aligned"
        ),
    ]
    
    # Generate cross-analysis insights
    insights = [
        InsightCard(
            id="ca_pending_settle",
            title=f"{auth_tx_count - settle_tx_count} transactions pending settlement",
            narrative=(
                f"Authorization report shows {auth_tx_count:,} transactions, while settlement "
                f"shows {settle_tx_count:,}. The {auth_tx_count - settle_tx_count} pending transactions "
                "are within normal T+2 settlement window. Monitor for delays beyond 72 hours."
            ),
            supporting_metrics=[
                SupportingMetric(label="Auth count", value=f"{auth_tx_count:,}"),
                SupportingMetric(label="Settled count", value=f"{settle_tx_count:,}"),
                SupportingMetric(label="Pending", value=f"{auth_tx_count - settle_tx_count}"),
            ],
            severity="info"
        ),
        InsightCard(
            id="ca_volume_variance",
            title="Volume variance within acceptable range",
            narrative=(
                f"Gross authorized volume (${auth_volume}M) vs net settled (${settle_volume}M) "
                f"shows ${round((auth_volume - settle_volume) * 1000, 1)}K variance. "
                "This is attributed to pending settlements and reversed transactions."
            ),
            supporting_metrics=[
                SupportingMetric(label="Auth volume", value=f"${auth_volume}M"),
                SupportingMetric(label="Settled volume", value=f"${settle_volume}M"),
                SupportingMetric(label="Variance", value=f"{round((1 - settle_volume/auth_volume) * 100, 1)}%"),
            ],
            severity="info"
        ),
    ]
    
    narrative = (
        f"Cross-analysis between authorization and settlement reports shows {recon_rate}% reconciliation rate. "
        f"All key metrics are within acceptable variance thresholds. "
        f"Pending settlements ({auth_tx_count - settle_tx_count} transactions) are within normal T+2 window."
    )
    
    return CrossAnalysisResponse(
        auth_report_id=request.auth_report_id,
        settlement_report_id=request.settlement_report_id,
        metrics=metrics,
        insights=insights,
        reconciliation_rate=recon_rate,
        narrative=narrative
    )


@router.get("/trends/{report_id}")
async def get_trends(report_id: str, metric: str = "all") -> dict:
    """
    Get trend analysis for a specific report.
    
    Analyzes historical data to identify:
    - Upward/downward trends
    - Seasonality patterns
    - Anomalies
    """
    _seed_random(report_id)
    
    trends = {
        "transactions": {
            "direction": "up",
            "change_percent": round(random.uniform(2, 8), 1),
            "period": "7d",
            "confidence": round(random.uniform(0.85, 0.95), 2)
        },
        "declines": {
            "direction": "up",
            "change_percent": round(random.uniform(5, 15), 1),
            "period": "7d",
            "confidence": round(random.uniform(0.78, 0.88), 2),
            "anomaly_detected": True,
            "anomaly_description": "Late-night decline spike detected (22:00-02:00 UTC)"
        },
        "settlement": {
            "direction": "stable",
            "change_percent": round(random.uniform(-1, 2), 1),
            "period": "7d",
            "confidence": round(random.uniform(0.88, 0.94), 2)
        },
        "interchange": {
            "direction": "up",
            "change_percent": round(random.uniform(2, 5), 1),
            "period": "7d",
            "confidence": round(random.uniform(0.82, 0.92), 2)
        }
    }
    
    if metric != "all" and metric in trends:
        return {"report_id": report_id, "trends": {metric: trends[metric]}}
    
    return {"report_id": report_id, "trends": trends}

