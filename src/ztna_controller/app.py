"""
ZTNA Controller (PDP) FastAPI Application.

Makes policy decisions based on risk scores and access context.
Implements default-deny Zero Trust principles.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.common.config import ZTNAControllerConfig, get_app_config
from src.common.logging import get_logger
from src.common.models import HealthResponse, PolicyRequest, PolicyResponse
from src.monitoring.metrics import (
    POLICY_DECISION_COUNTER,
    POLICY_DECISION_LATENCY,
)
from src.ztna_controller.pdp import ZTNAPolicyDecisionPoint

logger = get_logger("ztna_controller")

# Default PDP instance ready immediately
pdp: ZTNAPolicyDecisionPoint = ZTNAPolicyDecisionPoint(config=ZTNAControllerConfig())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for ZTNA Controller."""
    global pdp
    try:
        cfg = get_app_config()
        pdp = ZTNAPolicyDecisionPoint(config=cfg.ztna_controller)
        logger.info("ZTNA Controller PDP initialized from configuration")
    except Exception as e:
        logger.warning(f"Could not load config YAML, using default PDP config: {e}")
    yield


app = FastAPI(
    title="ZTNA Controller (PDP)",
    description="Policy Decision Point for Zero Trust Network Access",
    version="0.1.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested", extra={"extra_data": {"service": "ztna_controller"}})
    return HealthResponse(service="ztna-controller")


@app.post("/decide", response_model=PolicyResponse)
async def decide_policy(request: PolicyRequest) -> PolicyResponse:
    """Evaluate access request and return a definitive policy decision.

    Enforces Zero Trust Default-Deny and Least-Privilege.
    Measures and records policy decision latency.

    Args:
        request: PolicyRequest with user_id, risk_score, and access_context.

    Returns:
        PolicyResponse containing decision (ALLOW/RESTRICT/DENY), required MFA, and restrictions.
    """
    start_time = time.perf_counter()

    response = pdp.evaluate_policy(request)

    elapsed_seconds = time.perf_counter() - start_time

    # Record Prometheus metrics
    POLICY_DECISION_LATENCY.observe(elapsed_seconds)
    POLICY_DECISION_COUNTER.labels(decision=response.decision.value).inc()

    logger.info(
        "Policy decision rendered",
        extra={
            "extra_data": {
                "user_id": request.user_id,
                "risk_level": request.risk_score.level.value,
                "decision": response.decision.value,
                "latency_ms": response.latency_ms,
            }
        },
    )

    return response
