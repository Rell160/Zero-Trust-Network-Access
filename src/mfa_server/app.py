"""
MFA Server FastAPI Application.

Provides MFA enrollment, verification, and adaptive policy decision endpoints.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from src.common.config import MFAServerConfig, get_app_config
from src.common.logging import get_logger
from src.common.models import HealthResponse, MFAMethod, RiskLevel
from src.mfa_server.policy import AdaptiveMFAPolicy
from src.mfa_server.store import MFAStore
from src.mfa_server.totp import TOTPManager
from src.mfa_server.webauthn_sim import WebAuthnSimulator
from src.monitoring.metrics import (
    MFA_VERIFICATION_COUNTER,
    MFA_VERIFICATION_LATENCY,
)

logger = get_logger("mfa_server")

# Global instances with instant default initialization
store: MFAStore = MFAStore()
totp_manager: TOTPManager = TOTPManager(store=store, config=MFAServerConfig())
webauthn_sim: WebAuthnSimulator = WebAuthnSimulator(store=store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for MFA Server."""
    global store, totp_manager, webauthn_sim
    try:
        cfg = get_app_config()
        mfa_cfg = cfg.mfa_server
        totp_manager = TOTPManager(store=store, config=mfa_cfg)
    except Exception as e:
        logger.warning(f"Could not load config YAML, using default MFA config: {e}")
    logger.info("MFA Server services initialized successfully")
    yield


app = FastAPI(
    title="ZTNA MFA Server",
    description="Multi-Factor Authentication and Adaptive Policy service for ZTNA",
    version="0.1.0",
    lifespan=lifespan,
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# --- Request/Response Models ---

class PolicyQueryRequest(BaseModel):
    risk_level: RiskLevel


class PolicyQueryResponse(BaseModel):
    risk_level: RiskLevel
    required_factors: list[MFAMethod]
    mfa_required: bool
    policy_action: str  # ALLOW, STEP_UP_TOTP, STEP_UP_WEBAUTHN, DENY_QUARANTINE


class TOTPEnrollResponse(BaseModel):
    user_id: str
    secret: str
    provisioning_uri: str


class TOTPVerifyRequest(BaseModel):
    user_id: str
    code: str = Field(min_length=6, max_length=6)


class WebAuthnBeginRegistrationResponse(BaseModel):
    user_id: str
    challenge: str
    credential_id: str
    public_key_hex: str


class WebAuthnFinishRegistrationRequest(BaseModel):
    user_id: str
    signature: str


class WebAuthnBeginAssertionResponse(BaseModel):
    user_id: str
    challenge: str
    credential_id: str
    public_key_hex: str


class WebAuthnFinishAssertionRequest(BaseModel):
    user_id: str
    signature: str


class MFAVerifyResponse(BaseModel):
    user_id: str
    method: MFAMethod
    success: bool
    latency_ms: float
    message: str = ""


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested", extra={"extra_data": {"service": "mfa_server"}})
    return HealthResponse(service="mfa-server")


@app.post("/policy", response_model=PolicyQueryResponse)
async def query_adaptive_policy(req: PolicyQueryRequest) -> PolicyQueryResponse:
    """Query required authentication factors for a given risk level."""
    factors = AdaptiveMFAPolicy.get_required_factors(req.risk_level)
    mfa_req = AdaptiveMFAPolicy.is_mfa_required(req.risk_level)

    match req.risk_level:
        case RiskLevel.LOW:
            action = "ALLOW"
        case RiskLevel.MEDIUM:
            action = "STEP_UP_TOTP"
        case RiskLevel.HIGH:
            action = "STEP_UP_WEBAUTHN"
        case RiskLevel.CRITICAL:
            action = "DENY_QUARANTINE"

    return PolicyQueryResponse(
        risk_level=req.risk_level,
        required_factors=factors,
        mfa_required=mfa_req,
        policy_action=action,
    )


# --- TOTP Endpoints ---

@app.post("/totp/enroll/{user_id}", response_model=TOTPEnrollResponse)
async def enroll_totp(user_id: str) -> TOTPEnrollResponse:
    """Enroll a user with a new TOTP secret."""
    secret, uri = totp_manager.enroll(user_id)
    return TOTPEnrollResponse(user_id=user_id, secret=secret, provisioning_uri=uri)


@app.post("/totp/verify", response_model=MFAVerifyResponse)
async def verify_totp(req: TOTPVerifyRequest) -> MFAVerifyResponse:
    """Verify a TOTP code and measure response latency."""
    start_time = time.perf_counter()
    valid = totp_manager.verify(req.user_id, req.code)
    elapsed_seconds = time.perf_counter() - start_time
    elapsed_ms = elapsed_seconds * 1000.0

    # Prometheus metrics
    MFA_VERIFICATION_LATENCY.observe(elapsed_seconds)
    MFA_VERIFICATION_COUNTER.labels(
        method="totp", result="success" if valid else "failure"
    ).inc()

    logger.info(
        "TOTP verification",
        extra={
            "extra_data": {
                "user_id": req.user_id,
                "success": valid,
                "elapsed_ms": round(elapsed_ms, 3),
            }
        },
    )

    return MFAVerifyResponse(
        user_id=req.user_id,
        method=MFAMethod.TOTP,
        success=valid,
        latency_ms=round(elapsed_ms, 3),
        message="TOTP verified successfully" if valid else "Invalid TOTP code",
    )


# --- WebAuthn Endpoints ---

@app.post("/webauthn/register/begin/{user_id}", response_model=WebAuthnBeginRegistrationResponse)
async def begin_webauthn_registration(user_id: str) -> WebAuthnBeginRegistrationResponse:
    """Begin WebAuthn registration, returning challenge and keys."""
    reg = webauthn_sim.begin_registration(user_id)
    return WebAuthnBeginRegistrationResponse(**reg)


@app.post("/webauthn/register/finish", response_model=MFAVerifyResponse)
async def finish_webauthn_registration(
    req: WebAuthnFinishRegistrationRequest,
) -> MFAVerifyResponse:
    """Finish WebAuthn registration by verifying client assertion signature."""
    start = time.perf_counter()
    success = webauthn_sim.finish_registration(req.user_id, req.signature)
    elapsed_sec = time.perf_counter() - start
    elapsed_ms = elapsed_sec * 1000.0

    return MFAVerifyResponse(
        user_id=req.user_id,
        method=MFAMethod.WEBAUTHN,
        success=success,
        latency_ms=round(elapsed_ms, 3),
        message="Registration successful" if success else "Invalid registration signature",
    )


@app.post("/webauthn/auth/begin/{user_id}", response_model=WebAuthnBeginAssertionResponse)
async def begin_webauthn_assertion(user_id: str) -> WebAuthnBeginAssertionResponse:
    """Begin WebAuthn assertion challenge flow."""
    assertion = webauthn_sim.begin_assertion(user_id)
    if assertion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} has no registered WebAuthn credential",
        )
    return WebAuthnBeginAssertionResponse(**assertion)


@app.post("/webauthn/auth/finish", response_model=MFAVerifyResponse)
async def finish_webauthn_assertion(
    req: WebAuthnFinishAssertionRequest,
) -> MFAVerifyResponse:
    """Finish WebAuthn assertion and measure response latency."""
    start = time.perf_counter()
    success = webauthn_sim.finish_assertion(req.user_id, req.signature)
    elapsed_sec = time.perf_counter() - start
    elapsed_ms = elapsed_sec * 1000.0

    # Prometheus metrics
    MFA_VERIFICATION_LATENCY.observe(elapsed_sec)
    MFA_VERIFICATION_COUNTER.labels(
        method="webauthn", result="success" if success else "failure"
    ).inc()

    logger.info(
        "WebAuthn assertion",
        extra={
            "extra_data": {
                "user_id": req.user_id,
                "success": success,
                "elapsed_ms": round(elapsed_ms, 3),
            }
        },
    )

    return MFAVerifyResponse(
        user_id=req.user_id,
        method=MFAMethod.WEBAUTHN,
        success=success,
        latency_ms=round(elapsed_ms, 3),
        message="WebAuthn assertion passed" if success else "Invalid WebAuthn signature",
    )
