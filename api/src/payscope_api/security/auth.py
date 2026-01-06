from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException
from jose import jwt
from jose.exceptions import JWTError

from payscope_api.security.context import RequestContext
from payscope_api.security.roles import Role


def _jwt_key() -> str:
    key = os.getenv("JWT_PUBLIC_KEY")
    if not key:
        raise RuntimeError("JWT_PUBLIC_KEY not configured")
    return key


def get_request_context(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_bank_id: Optional[str] = Header(default=None, alias="X-Bank-Id"),
) -> RequestContext:
    """
    API-layer auth:
      - expects Bearer JWT with claims: sub, role, bank_id
      - bank_id header must match claim if provided (prevents confused deputy)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    token = authorization.split(" ", 1)[1].strip()

    try:
        claims = jwt.decode(token, _jwt_key(), algorithms=["RS256", "EdDSA"], options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")

    sub = str(claims.get("sub") or "")
    role_s = str(claims.get("role") or "")
    bank_id = str(claims.get("bank_id") or "")

    if not sub or not role_s or not bank_id:
        raise HTTPException(status_code=401, detail="missing_claims")

    if x_bank_id and x_bank_id != bank_id:
        raise HTTPException(status_code=403, detail="bank_id_mismatch")

    try:
        role = Role(role_s)
    except Exception:
        raise HTTPException(status_code=403, detail="invalid_role")

    return RequestContext(subject=sub, role=role, bank_id=bank_id)




