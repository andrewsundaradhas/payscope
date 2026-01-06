from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    BANK_ADMIN = "BANK_ADMIN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"
    SYSTEM = "SYSTEM"




