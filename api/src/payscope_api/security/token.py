from __future__ import annotations

import os
import time
from typing import Dict

from jose import jwt

from payscope_api.security.roles import Role


def issue_token(*, subject: str, role: Role, bank_id: str, ttl_seconds: int = 3600) -> str:
    """
    Issues a JWT signed with the private key in JWT_PRIVATE_KEY (PEM).
    Claims: sub, role, bank_id, exp.
    """
    priv = os.getenv("JWT_PRIVATE_KEY")
    if not priv:
        raise RuntimeError("JWT_PRIVATE_KEY not configured")
    now = int(time.time())
    payload: Dict[str, object] = {
        "sub": subject,
        "role": role.value,
        "bank_id": bank_id,
        "exp": now + ttl_seconds,
        "iat": now,
    }
    return jwt.encode(payload, priv, algorithm="RS256")




