from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import redis


@dataclass(frozen=True)
class CacheConfig:
    url: str
    ttl_s: int = 60


class TenantCache:
    """
    Tenant-safe cache:
      - keys are prefixed with bank_id (tenant isolation)
      - values are JSON
      - deterministic ordering ensured by callers
    """

    def __init__(self, cfg: CacheConfig):
        self._r = redis.Redis.from_url(cfg.url, decode_responses=True)
        self._ttl = cfg.ttl_s

    def get_json(self, *, bank_id: str, key: str) -> Optional[Dict[str, Any]]:
        v = self._r.get(f"{bank_id}:{key}")
        return json.loads(v) if v else None

    def set_json(self, *, bank_id: str, key: str, value: Dict[str, Any], ttl_s: int | None = None) -> None:
        self._r.setex(f"{bank_id}:{key}", ttl_s or self._ttl, json.dumps(value, ensure_ascii=False, sort_keys=True))




