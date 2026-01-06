from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from payscope_api.security.auth import get_request_context
from payscope_api.security.context import RequestContext
from payscope_api.security.rbac import AccessDenied, POLICY_QUERY, POLICY_SIMULATION
try:
    from payscope_api.insights import router as insights_router
except ImportError:
    insights_router = None

try:
    from payscope_api.chat_router import router as chat_router
except ImportError:
    chat_router = None

try:
    from payscope_api.chat.router import router as chat_query_router
except ImportError:
    chat_query_router = None

try:
    from payscope_api.reports import router as reports_router
except ImportError:
    reports_router = None

try:
    from payscope_api.health import router as health_router
except ImportError:
    health_router = None

try:
    from payscope_api.metrics import router as metrics_router
except ImportError:
    metrics_router = None

# Optional admin import (requires asyncpg, neo4j, pinecone)
try:
    from payscope_api.admin import validate_datasets
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False
    validate_datasets = None


def _log(component: str, event: str, severity: str, tenant_id: str) -> None:
    logging.getLogger("payscope_api").info(
        json.dumps(
            {
                "component": component,
                "event": event,
                "severity": severity,
                "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
    )


app = FastAPI(title="PayScope API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (if available)
if insights_router:
    app.include_router(insights_router, prefix="/api")
if chat_router:
    app.include_router(chat_router, prefix="/api")
if chat_query_router:
    app.include_router(chat_query_router, prefix="/api")
if reports_router:
    app.include_router(reports_router, prefix="/api")
if health_router:
    app.include_router(health_router)
if metrics_router:
    app.include_router(metrics_router)


@app.post("/secure/query")
def secure_query(ctx: RequestContext = Depends(get_request_context)) -> dict:
    try:
        POLICY_QUERY.check(ctx)
    except AccessDenied:
        _log("security", "access_denied", "WARN", ctx.bank_id)
        raise HTTPException(status_code=403, detail="access_denied")
    return {"ok": True, "bank_id": ctx.bank_id, "role": ctx.role.value}


@app.post("/secure/simulation")
def secure_simulation(ctx: RequestContext = Depends(get_request_context)) -> dict:
    try:
        POLICY_SIMULATION.check(ctx)
    except AccessDenied:
        _log("security", "access_denied", "WARN", ctx.bank_id)
        raise HTTPException(status_code=403, detail="access_denied")
    return {"ok": True, "bank_id": ctx.bank_id, "role": ctx.role.value}


@app.get("/admin/validate-datasets")
async def admin_validate_datasets(ctx: RequestContext = Depends(get_request_context)) -> dict:
    """Admin endpoint to validate dataset counts per bank."""
    if not ADMIN_AVAILABLE or validate_datasets is None:
        raise HTTPException(
            status_code=503, 
            detail="Admin functionality unavailable - missing dependencies (asyncpg, neo4j, pinecone)"
        )
    return await validate_datasets(ctx)


