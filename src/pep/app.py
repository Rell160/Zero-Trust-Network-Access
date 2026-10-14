"""
Policy Enforcement Point (PEP) FastAPI Application.

Acts as a reverse proxy that enforces policy decisions from the PDP.
All incoming requests are evaluated before being forwarded upstream.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Response, status
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from src.common.config import PEPConfig, get_app_config
from src.common.logging import get_logger
from src.common.models import AccessContext, HealthResponse, MFAMethod
from src.monitoring.metrics import PEP_REQUEST_COUNTER, PEP_REQUEST_LATENCY
from src.pep.proxy import PolicyEnforcementPoint

logger = get_logger("pep")

# Global PEP proxy instance
pep_proxy: PolicyEnforcementPoint = PolicyEnforcementPoint(config=PEPConfig())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for PEP."""
    global pep_proxy
    try:
        cfg = get_app_config()
        pep_proxy = PolicyEnforcementPoint(config=cfg.pep)
        logger.info("PEP Proxy initialized from configuration")
    except Exception as e:
        logger.warning(f"Could not load config YAML, using default PEP config: {e}")
    yield


app = FastAPI(
    title="ZTNA Policy Enforcement Point",
    description="Reverse proxy enforcing Zero Trust policy decisions",
    version="0.1.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


class PEPEnforceRequest(BaseModel):
    """Incoming request to PEP for policy enforcement."""

    context: AccessContext
    session_id: str = ""
    mfa_verified: bool = False
    mfa_method: MFAMethod = MFAMethod.NONE


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested", extra={"extra_data": {"service": "pep"}})
    return HealthResponse(service="pep")


@app.post("/enforce")
async def enforce_access(req: PEPEnforceRequest, response: Response):
    """Enforce complete ZTNA pipeline on an incoming access request.

    Evaluates:
      1. Context via Risk Engine
      2. Decision via ZTNA Controller (PDP)
      3. MFA condition check
      4. Restriction enforcement (Read-only, quarantine, allow)

    Returns:
      HTTP 200: Access allowed (full or restricted)
      HTTP 401: Additional MFA required
      HTTP 403: Access Denied / Quarantined
      HTTP 503: Subsystem unavailable (Default-Deny)
    """
    start_time = time.perf_counter()

    result = await pep_proxy.enforce(
        context=req.context,
        session_id=req.session_id,
        mfa_verified=req.mfa_verified,
        mfa_method_used=req.mfa_method,
    )

    elapsed_seconds = time.perf_counter() - start_time
    http_code = result.get("http_status", 500)
    response.status_code = http_code

    # Record Prometheus metrics
    PEP_REQUEST_LATENCY.observe(elapsed_seconds)
    PEP_REQUEST_COUNTER.labels(
        method="POST", status=str(http_code)
    ).inc()

    logger.info(
        "PEP enforcement executed",
        extra={
            "extra_data": {
                "user_id": req.context.user_id,
                "status": result.get("status"),
                "http_status": http_code,
                "latency_ms": result.get("latency_ms"),
            }
        },
    )

    return result
