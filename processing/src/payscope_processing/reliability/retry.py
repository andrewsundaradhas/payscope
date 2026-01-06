from __future__ import annotations

import random


def backoff_with_jitter(attempt: int, *, base_s: int = 2, cap_s: int = 300) -> int:
    """
    Exponential backoff with full jitter.
    Deterministic-ish with seeded RNG in tests; production uses system randomness.
    """
    exp = min(cap_s, base_s * (2 ** max(0, attempt)))
    return int(random.uniform(0, exp))




