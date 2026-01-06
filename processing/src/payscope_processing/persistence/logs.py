from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


def log_stage(stage: str, bank_id: str, report_id: str, status: str) -> None:
    logging.getLogger("persistence").info(
        json.dumps(
            {
                "stage": stage,
                "bank_id": bank_id,
                "report_id": report_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
    )




