from __future__ import annotations

from typing import Dict

from payscope_processing.graph.neo4j_writer import GraphWriter, Neo4jConfig
from payscope_processing.graph.reasoning import LifecycleStageInfo, upsert_graph_with_anomalies, LifecycleAnomalies
from payscope_processing.normalize.schema import NormalizationResult
from payscope_processing.persistence.logs import log_stage


def persist_graph(
    *,
    cfg: Neo4jConfig,
    bank_id: str,
    norm: NormalizationResult,
) -> None:
    writer = GraphWriter(cfg)
    try:
        # One Transaction node per transaction_id per bank.
        for tx in norm.transactions:
            stages = [
                LifecycleStageInfo(
                    stage=tx.lifecycle_stage.value,
                    amount=float(tx.amount),
                    currency=tx.currency,
                    timestamp_utc=tx.timestamp_utc,
                )
            ]
            # We do not recompute anomalies; set defaults (all false).
            anomalies = LifecycleAnomalies(
                has_amount_mismatch=False,
                missing_settlement=False,
                currency_conflict=False,
                lifecycle_gap_duration=None,
                timestamp_violation=False,
            )
            writer.upsert_lifecycle(
                transaction_pk=f"{bank_id}:{tx.transaction_id}",
                transaction_id=tx.transaction_id,
                merchant_pk=f"{bank_id}:{tx.merchant_id}",
                bank_pk=None,
                network=tx.card_network,
                stages=[
                    {
                        "rel_type": "AUTHORIZED",
                        "stage": tx.lifecycle_stage.value,
                        "event_time": tx.timestamp_utc.isoformat(),
                    }
                ],
            )
            # store anomalies flags
            writer._driver.session().run(
                """
                MATCH (t:Transaction {transaction_pk: $pk})
                SET t.bank_id = $bank_id,
                    t.has_amount_mismatch = $ham,
                    t.missing_settlement = $ms,
                    t.currency_conflict = $cc,
                    t.lifecycle_gap_duration = $lgd,
                    t.timestamp_violation = $tv
                """,
                pk=f"{bank_id}:{tx.transaction_id}",
                bank_id=bank_id,
                ham=anomalies.has_amount_mismatch,
                ms=anomalies.missing_settlement,
                cc=anomalies.currency_conflict,
                lgd=anomalies.lifecycle_gap_duration,
                tv=anomalies.timestamp_violation,
            )
        log_stage("neo4j", bank_id, str(norm.report_fact.report_id), "success")
    finally:
        writer.close()




