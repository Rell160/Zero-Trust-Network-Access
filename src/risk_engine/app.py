"""
Risk Engine FastAPI Application.

Provides risk scoring for access requests based on contextual features.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from src.common.config import get_app_config
from src.common.logging import get_logger
from src.common.models import AccessContext, HealthResponse, RiskScore
from src.monitoring.metrics import (
    RISK_EVALUATION_LATENCY,
    RISK_LEVEL_COUNTER,
    RISK_SCORE_HISTOGRAM,
)
from src.risk_engine.engine import RiskScoringEngine

logger = get_logger("risk_engine")

# Global engine instance
engine: RiskScoringEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    global engine
    try:
        config = get_app_config()
        engine = RiskScoringEngine.from_config(config.risk_engine)
        logger.info("Risk Engine initialized successfully from config")
    except Exception as e:
        logger.warning(f"Could not load config YAML, using default engine: {e}")
        engine = RiskScoringEngine()
    yield


app = FastAPI(
    title="ZTNA Risk Engine",
    description="Risk scoring service for Zero Trust Network Access",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested", extra={"extra_data": {"service": "risk_engine"}})
    return HealthResponse(service="risk-engine")


@app.post("/evaluate", response_model=RiskScore)
async def evaluate_risk(context: AccessContext) -> RiskScore:
    """Evaluate risk for an incoming access context.

    Calculates normalized scores for 7 contextual features,
    aggregates with configured weights, classifies risk level,
    and records Prometheus metrics.

    Args:
        context: Access context containing user, device, network, and request details.

    Returns:
        RiskScore with score, level, feature contributions, and explanation.
    """
    global engine
    if engine is None:
        engine = RiskScoringEngine()

    start_time = time.perf_counter()

    result = engine.evaluate(context)

    duration_seconds = time.perf_counter() - start_time

    # Record Prometheus metrics
    RISK_SCORE_HISTOGRAM.observe(result.score)
    RISK_EVALUATION_LATENCY.observe(duration_seconds)
    RISK_LEVEL_COUNTER.labels(level=result.level.value).inc()

    return result
