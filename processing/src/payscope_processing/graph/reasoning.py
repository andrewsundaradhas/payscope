from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from payscope_processing.graph.neo4j_writer import GraphWriter


@dataclass(frozen=True)
class LifecycleStageInfo:
    stage: str  # AUTH|CLEARING|SETTLEMENT
    amount: float
    currency: str
    timestamp_utc: datetime


@dataclass(frozen=True)
class LifecycleAnomalies:
    has_amount_mismatch: bool
    missing_settlement: bool
    currency_conflict: bool
    lifecycle_gap_duration: float | None  # seconds
    timestamp_violation: bool


def analyze_lifecycle(stages: List[LifecycleStageInfo]) -> LifecycleAnomalies:
    """
    Detects lifecycle anomalies:
      - missing settlement
      - amount mismatch across stages (> 1% relative difference)
      - currency mismatch
      - timestamp ordering violations
      - lifecycle gap duration (auth -> settlement) if both exist
    """
    by_stage = {s.stage: s for s in stages}
    missing_settlement = "SETTLEMENT" not in by_stage

    currencies = {s.currency for s in stages}
    currency_conflict = len(currencies) > 1

    amounts = [s.amount for s in stages]
    has_amount_mismatch = False
    if len(amounts) >= 2:
        for i in range(len(amounts)):
            for j in range(i + 1, len(amounts)):
                a, b = amounts[i], amounts[j]
                if a == 0 or b == 0:
                    continue
                rel = abs(a - b) / max(abs(a), abs(b))
                if rel > 0.01:  # >1% mismatch
                    has_amount_mismatch = True

    # Timestamp order: AUTH <= CLEARING <= SETTLEMENT
    order = ["AUTH", "CLEARING", "SETTLEMENT"]
    ts_list = []
    for st in order:
        if st in by_stage:
            ts_list.append(by_stage[st].timestamp_utc)
    timestamp_violation = any(ts_list[i] > ts_list[i + 1] for i in range(len(ts_list) - 1))

    lifecycle_gap_duration = None
    if "AUTH" in by_stage and "SETTLEMENT" in by_stage:
        lifecycle_gap_duration = (by_stage["SETTLEMENT"].timestamp_utc - by_stage["AUTH"].timestamp_utc).total_seconds()

    return LifecycleAnomalies(
        has_amount_mismatch=has_amount_mismatch,
        missing_settlement=missing_settlement,
        currency_conflict=currency_conflict,
        lifecycle_gap_duration=lifecycle_gap_duration,
        timestamp_violation=timestamp_violation,
    )


def upsert_graph_with_anomalies(
    *,
    writer: GraphWriter,
    transaction_pk: str,
    transaction_id: str,
    merchant_pk: str,
    bank_pk: str | None,
    network: str,
    stages: List[LifecycleStageInfo],
) -> LifecycleAnomalies:
    """
    Builds lifecycle edges AUTH->CLEARING->SETTLEMENT and writes anomaly flags on the Transaction node.
    """
    anomalies = analyze_lifecycle(stages)

    # Write edges with temporal ordering enforced by writer
    writer.upsert_lifecycle(
        transaction_pk=transaction_pk,
        transaction_id=transaction_id,
        merchant_pk=merchant_pk,
        bank_pk=bank_pk,
        network=network,
        stages=[
            {
                "rel_type": _rel_for_stage(s.stage),
                "stage": s.stage,
                "event_time": s.timestamp_utc.isoformat(),
            }
            for s in stages
        ],
    )

    # Set anomaly properties on the transaction node
    with writer._driver.session() as session:  # internal driver used intentionally
        session.run(
            """
            MATCH (t:Transaction {transaction_pk: $transaction_pk})
            SET t.has_amount_mismatch = $has_amount_mismatch,
                t.missing_settlement = $missing_settlement,
                t.currency_conflict = $currency_conflict,
                t.lifecycle_gap_duration = $lifecycle_gap_duration,
                t.timestamp_violation = $timestamp_violation
            """,
            transaction_pk=transaction_pk,
            has_amount_mismatch=anomalies.has_amount_mismatch,
            missing_settlement=anomalies.missing_settlement,
            currency_conflict=anomalies.currency_conflict,
            lifecycle_gap_duration=anomalies.lifecycle_gap_duration,
            timestamp_violation=anomalies.timestamp_violation,
        )

    return anomalies


def _rel_for_stage(stage: str) -> str:
    if stage == "AUTH":
        return "AUTHORIZED"
    if stage == "CLEARING":
        return "CLEARED"
    if stage == "SETTLEMENT":
        return "SETTLED"
    return "FLOW"




