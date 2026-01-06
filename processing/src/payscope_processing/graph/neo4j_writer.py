from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neo4j import GraphDatabase


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str
    user: str
    password: str


class GraphWriter:
    """
    Idempotent graph writer.

    Node types: Transaction, Merchant, Bank, Network
    Edge types: AUTHORIZED, CLEARED, SETTLED, DISPUTED

    Duplicate prevention:
      - nodes are MERGE'd by unique keys (transaction_pk, merchant_pk, bank_pk, network name)
      - edges are MERGE'd by unique edge_id

    Temporal ordering:
      - this writer enforces non-decreasing event_time across stage edges if multiple are written.
    """

    def __init__(self, cfg: Neo4jConfig):
        self._driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))

    def close(self) -> None:
        self._driver.close()

    def upsert_lifecycle(
        self,
        *,
        transaction_pk: str,
        transaction_id: str,
        merchant_pk: str,
        bank_pk: str | None,
        network: str,
        stages: list[dict[str, Any]],
    ) -> None:
        """
        stages: list of {rel_type: 'AUTHORIZED'|'CLEARED'|'SETTLED'|'DISPUTED', stage: 'AUTH'|'CLEARING'|'SETTLEMENT', event_time: iso8601}
        """
        with self._driver.session() as session:
            session.execute_write(
                self._write_lifecycle,
                transaction_pk,
                transaction_id,
                merchant_pk,
                bank_pk,
                network,
                stages,
            )

    @staticmethod
    def _write_lifecycle(tx, transaction_pk: str, transaction_id: str, merchant_pk: str, bank_pk: str | None, network: str, stages: list[dict[str, Any]]):
        # Create/merge nodes
        tx.run(
            """
            MERGE (t:Transaction {transaction_pk: $transaction_pk})
              ON CREATE SET t.transaction_id = $transaction_id
              ON MATCH SET t.transaction_id = $transaction_id
            MERGE (m:Merchant {merchant_pk: $merchant_pk})
            MERGE (n:Network {name: $network})
            MERGE (t)-[:OF_NETWORK]->(n)
            MERGE (t)-[:AT_MERCHANT]->(m)
            """,
            transaction_pk=transaction_pk,
            transaction_id=transaction_id,
            merchant_pk=merchant_pk,
            network=network,
        )

        if bank_pk:
            tx.run(
                """
                MERGE (b:Bank {bank_pk: $bank_pk})
                MATCH (t:Transaction {transaction_pk: $transaction_pk})
                MERGE (t)-[:AT_BANK]->(b)
                """,
                bank_pk=bank_pk,
                transaction_pk=transaction_pk,
            )

        # Sort stages by event_time to enforce ordering deterministically
        def parse_time(s: str) -> datetime:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))

        ordered = sorted(stages, key=lambda x: parse_time(str(x["event_time"])))

        last_time = None
        for s in ordered:
            rel_type = str(s["rel_type"])
            stage = str(s["stage"])
            event_time = str(s["event_time"])
            if last_time and parse_time(event_time) < last_time:
                raise ValueError("temporal_ordering_violation")
            last_time = parse_time(event_time)

            edge_id = f"{transaction_pk}|{rel_type}|{stage}"
            tx.run(
                f"""
                MATCH (t:Transaction {{transaction_pk: $transaction_pk}})
                MERGE (t)-[r:{rel_type} {{edge_id: $edge_id}}]->(t)
                  ON CREATE SET r.stage = $stage, r.event_time = $event_time
                  ON MATCH SET r.stage = $stage, r.event_time = $event_time
                """,
                transaction_pk=transaction_pk,
                edge_id=edge_id,
                stage=stage,
                event_time=event_time,
            )




