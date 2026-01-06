from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def set_trace_id(trace_id: str | None) -> None:
    trace_id_var.set(trace_id)


def get_trace_id() -> str | None:
    return trace_id_var.get()


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": self._service_name,
            "log_level": record.levelname,
            "trace_id": getattr(record, "trace_id", None) or get_trace_id(),
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = getattr(record, "trace_id", None) or get_trace_id()
        return True


def configure_logging(service_name: str, level: str | int | None = None) -> None:
    resolved_level: int
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    if isinstance(level, int):
        resolved_level = level
    else:
        resolved_level = logging.getLevelName(level.upper())
        if not isinstance(resolved_level, int):
            resolved_level = logging.INFO

    root = logging.getLogger()
    root.setLevel(resolved_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(JsonFormatter(service_name=service_name))
    handler.addFilter(TraceIdFilter())

    root.handlers.clear()
    root.addHandler(handler)




