"""
Unit and integration tests for the MFA Server & Adaptive MFA Policy.

Tests:
  - Adaptive MFA Policy resolution per RiskLevel (Low, Medium, High, Critical)
  - In-memory MFAStore operations
  - TOTP enrollment, URI generation, and code verification
  - WebAuthn/FIDO2 simulator registration and assertion verification
  - FastAPI endpoint testing for /policy, /totp, and /webauthn
"""

from __future__ import annotations

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient

from src.common.config import MFAServerConfig
from src.common.models import MFAMethod, RiskLevel
from src.mfa_server.app import app
from src.mfa_server.policy import AdaptiveMFAPolicy
from src.mfa_server.store import MFAStore
from src.mfa_server.totp import TOTPManager
from src.mfa_server.webauthn_sim import WebAuthnSimulator


# =====================================================================
# Adaptive Policy Tests
# =====================================================================

def test_adaptive_policy_low_risk():
    """LOW risk requires only password, no MFA step-up."""
    factors = AdaptiveMFAPolicy.get_required_factors(RiskLevel.LOW)
    assert factors == [MFAMethod.PASSWORD]
    assert not AdaptiveMFAPolicy.is_mfa_required(RiskLevel.LOW)


def test_adaptive_policy_medium_risk():
    """MEDIUM risk requires step-up with TOTP."""
    factors = AdaptiveMFAPolicy.get_required_factors(RiskLevel.MEDIUM)
    assert factors == [MFAMethod.PASSWORD, MFAMethod.TOTP]
    assert AdaptiveMFAPolicy.is_mfa_required(RiskLevel.MEDIUM)


def test_adaptive_policy_high_risk():
    """HIGH risk requires strong WebAuthn/FIDO2 authentication."""
    factors = AdaptiveMFAPolicy.get_required_factors(RiskLevel.HIGH)
    assert factors == [MFAMethod.PASSWORD, MFAMethod.WEBAUTHN]
    assert AdaptiveMFAPolicy.is_mfa_required(RiskLevel.HIGH)


def test_adaptive_policy_critical_risk():
    """CRITICAL risk returns empty factors (access denied, quarantine)."""
    factors = AdaptiveMFAPolicy.get_required_factors(RiskLevel.CRITICAL)
    assert factors == []
    assert not AdaptiveMFAPolicy.is_mfa_required(RiskLevel.CRITICAL)


# =====================================================================
# TOTP Manager Tests
# =====================================================================

def test_totp_enrollment_and_verification():
    """User can enroll TOTP and verify a valid generated code."""
    store = MFAStore()
    config = MFAServerConfig(issuer_name="TestIssuer", totp_digits=6, totp_interval_seconds=30)
    manager = TOTPManager(store=store, config=config)

    user_id = "alice"
    secret, uri = manager.enroll(user_id)

    assert secret is not None
    assert len(secret) >= 16
    assert "otpauth://" in uri
    assert "TestIssuer" in uri
    assert store.has_totp(user_id)

    # Generate valid current code
    totp_generator = pyotp.TOTP(secret)
    current_code = totp_generator.now()

    # Verify correct code
    assert manager.verify(user_id, current_code) is True

    # Verify incorrect code
    assert manager.verify(user_id, "000000") is False

    # Verify non-enrolled user
    assert manager.verify("unknown_user", current_code) is False


# =====================================================================
# WebAuthn Simulator Tests
# =====================================================================

def test_webauthn_registration_and_assertion_flow():
    """Full WebAuthn simulator lifecycle: registration and authentication assertion."""
    store = MFAStore()
    sim = WebAuthnSimulator(store=store)
    user_id = "bob"

    # Step 1: Registration Begin
    reg_data = sim.begin_registration(user_id)
    assert reg_data["user_id"] == user_id
    assert "challenge" in reg_data
    assert "credential_id" in reg_data
    assert "public_key_hex" in reg_data

    # Client computes signature
    sig = WebAuthnSimulator.compute_signature(
        challenge=reg_data["challenge"],
        public_key_hex=reg_data["public_key_hex"],
    )

    # Step 2: Registration Finish
    reg_success = sim.finish_registration(user_id, sig)
    assert reg_success is True
    assert store.has_webauthn(user_id) is True

    # Step 3: Assertion Begin
    auth_data = sim.begin_assertion(user_id)
    assert auth_data is not None
    assert auth_data["user_id"] == user_id
    assert auth_data["credential_id"] == reg_data["credential_id"]

    # Client computes auth signature
    auth_sig = WebAuthnSimulator.compute_signature(
        challenge=auth_data["challenge"],
        public_key_hex=auth_data["public_key_hex"],
    )

    # Step 4: Assertion Finish
    auth_success = sim.finish_assertion(user_id, auth_sig)
    assert auth_success is True

    # Step 5: Test invalid assertion signature
    auth_data_2 = sim.begin_assertion(user_id)
    assert auth_data_2 is not None
    invalid_sig = "deadbeef" * 8
    assert sim.finish_assertion(user_id, invalid_sig) is False


# =====================================================================
# API Endpoints Integration Tests
# =====================================================================

@pytest.mark.asyncio
async def test_api_policy_endpoint():
    """POST /policy returns correct required factors per risk level."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # LOW
        resp_low = await client.post("/policy", json={"risk_level": "low"})
        assert resp_low.status_code == 200
        assert resp_low.json()["policy_action"] == "ALLOW"

        # MEDIUM
        resp_med = await client.post("/policy", json={"risk_level": "medium"})
        assert resp_med.status_code == 200
        assert resp_med.json()["policy_action"] == "STEP_UP_TOTP"
        assert "totp" in resp_med.json()["required_factors"]

        # HIGH
        resp_high = await client.post("/policy", json={"risk_level": "high"})
        assert resp_high.status_code == 200
        assert resp_high.json()["policy_action"] == "STEP_UP_WEBAUTHN"
        assert "webauthn" in resp_high.json()["required_factors"]

        # CRITICAL
        resp_crit = await client.post("/policy", json={"risk_level": "critical"})
        assert resp_crit.status_code == 200
        assert resp_crit.json()["policy_action"] == "DENY_QUARANTINE"


@pytest.mark.asyncio
async def test_api_totp_flow():
    """API endpoints /totp/enroll and /totp/verify operate properly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Enroll
        enroll_resp = await client.post("/totp/enroll/charlie")
        assert enroll_resp.status_code == 200
        data = enroll_resp.json()
        secret = data["secret"]

        # Generate valid code
        code = pyotp.TOTP(secret).now()

        # Verify
        verify_resp = await client.post(
            "/totp/verify", json={"user_id": "charlie", "code": code}
        )
        assert verify_resp.status_code == 200
        v_data = verify_resp.json()
        assert v_data["success"] is True
        assert v_data["latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_api_webauthn_flow():
    """API endpoints /webauthn register and assertion flows operate properly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register begin
        reg_begin = await client.post("/webauthn/register/begin/dave")
        assert reg_begin.status_code == 200
        reg_data = reg_begin.json()

        # Compute signature
        sig = WebAuthnSimulator.compute_signature(
            reg_data["challenge"], reg_data["public_key_hex"]
        )

        # 2. Register finish
        reg_finish = await client.post(
            "/webauthn/register/finish",
            json={"user_id": "dave", "signature": sig},
        )
        assert reg_finish.status_code == 200
        assert reg_finish.json()["success"] is True

        # 3. Auth begin
        auth_begin = await client.post("/webauthn/auth/begin/dave")
        assert auth_begin.status_code == 200
        auth_data = auth_begin.json()

        auth_sig = WebAuthnSimulator.compute_signature(
            auth_data["challenge"], auth_data["public_key_hex"]
        )

        # 4. Auth finish
        auth_finish = await client.post(
            "/webauthn/auth/finish",
            json={"user_id": "dave", "signature": auth_sig},
        )
        assert auth_finish.status_code == 200
        assert auth_finish.json()["success"] is True
        assert auth_finish.json()["latency_ms"] >= 0.0
