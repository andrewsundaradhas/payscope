from __future__ import annotations

from dataclasses import dataclass

from payscope_api.security.roles import Role


@dataclass(frozen=True)
class RequestContext:
    subject: str
    role: Role
    bank_id: str  # tenant id (UUID string)




