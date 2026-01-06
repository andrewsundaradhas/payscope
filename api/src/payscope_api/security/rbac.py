from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from payscope_api.security.context import RequestContext
from payscope_api.security.roles import Role


class AccessDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class Policy:
    name: str
    allowed_roles: tuple[Role, ...]

    def check(self, ctx: RequestContext) -> None:
        if ctx.role not in self.allowed_roles:
            raise AccessDenied(f"access_denied policy={self.name} role={ctx.role}")


# API layer policies (explicit, no implicit permissions)
POLICY_QUERY = Policy("query", (Role.ADMIN, Role.BANK_ADMIN, Role.ANALYST, Role.AUDITOR))
POLICY_SIMULATION = Policy("simulation", (Role.ADMIN, Role.BANK_ADMIN, Role.ANALYST))
POLICY_ADMIN = Policy("admin", (Role.ADMIN, Role.BANK_ADMIN))
POLICY_SYSTEM = Policy("system", (Role.SYSTEM, Role.ADMIN))




