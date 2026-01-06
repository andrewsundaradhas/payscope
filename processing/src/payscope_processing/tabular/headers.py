from __future__ import annotations

import re


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_headers(raw: list[str]) -> list[str]:
    """
    Normalize headers:
      - lowercase
      - snake_case
      - deduplicate
    """
    normed: list[str] = []
    seen: dict[str, int] = {}

    for i, h in enumerate(raw):
        base = _normalize_one(h if h is not None else "")
        if not base:
            base = f"col_{i+1}"
        n = seen.get(base, 0) + 1
        seen[base] = n
        normed.append(base if n == 1 else f"{base}_{n}")
    return normed


def _normalize_one(s: str) -> str:
    t = (s or "").strip().lower()
    t = _NON_ALNUM.sub("_", t)
    t = t.strip("_")
    t = re.sub(r"_+", "_", t)
    return t




