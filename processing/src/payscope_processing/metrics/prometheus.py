from __future__ import annotations

from prometheus_client import Counter, Histogram


ingestion_latency = Histogram("ingestion_latency_seconds", "Upload to parse enqueue latency")
job_failure_rate = Counter("job_failure_total", "Count of failed jobs", ["job_name"])
agent_conflict_rate = Counter("agent_conflict_total", "Count of agent conflicts", ["task_type"])
query_latency = Histogram("query_latency_seconds", "RAG query latency")




