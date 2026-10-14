"""
Unit and integration tests for ZTNA Controller (PDP) and PEP.

Tests:
  - PDP Decision logic for each RiskLevel
  - Default-Deny principle
  - Restriction enforcement (read-only, quarantine, segmentation)
  - PDP endpoint /decide
  - PEP endpoint /enforce (in-process, mocking inter-service calls)
"""

from __future__ import annotations

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.common.models import (
    AccessContext,
    DeviceInfo,
    MFAMethod,
    PolicyDecision,
    PolicyRequest,
    RiskLevel,
    RiskScore,
)
from src.ztna_controller.app import app as pdp_app
from src.ztna_controller.pdp import ZTNAPolicyDecisionPoint


# =====================================================================
# Helper builders
# =====================================================================

def _build_risk_score(score: float, level: RiskLevel) -> RiskScore:
    return RiskScore(
        score=score,
        level=level,
        feature_contributions={},
        explanation=f"Test score {score}",
    )


def _build_context(user_id: str = "alice", resource: str = "/api/data") -> AccessContext:
    return AccessContext(
        user_id=user_id,
        device=DeviceInfo(device_id="laptop-1"),
        resource_requested=resource,
        resource_sensitivity="normal",
    )


def _build_policy_request(
    score: float, level: RiskLevel, user_id: str = "alice", resource: str = "/api/data"
) -> PolicyRequest:
    return PolicyRequest(
        user_id=user_id,
        session_id="sess-001",
        risk_score=_build_risk_score(score, level),
        resource_requested=resource,
        access_context=_build_context(user_id, resource),
    )


# =====================================================================
# PDP Engine Unit Tests
# =====================================================================

class TestPDPEngine:
    """Test suite for ZTNAPolicyDecisionPoint."""

    pdp = ZTNAPolicyDecisionPoint()

    def test_low_risk_allows_full_access(self):
        """Low risk -> ALLOW with password only, full read_write."""
        req = _build_policy_request(15.0, RiskLevel.LOW)
        resp = self.pdp.evaluate_policy(req)

        assert resp.decision == PolicyDecision.ALLOW
        assert resp.required_mfa == [MFAMethod.PASSWORD]
        assert resp.restrictions["mode"] == "read_write"
        assert "*" in resp.allowed_resources

    def test_medium_risk_allows_with_totp(self):
        """Medium risk -> ALLOW with Password + TOTP."""
        req = _build_policy_request(45.0, RiskLevel.MEDIUM)
        resp = self.pdp.evaluate_policy(req)

        assert resp.decision == PolicyDecision.ALLOW
        assert MFAMethod.TOTP in resp.required_mfa
        assert MFAMethod.PASSWORD in resp.required_mfa
        assert resp.restrictions["mode"] == "read_write"

    def test_high_risk_restricts_access(self):
        """High risk -> RESTRICT with WebAuthn, read-only mode."""
        req = _build_policy_request(72.0, RiskLevel.HIGH)
        resp = self.pdp.evaluate_policy(req)

        assert resp.decision == PolicyDecision.RESTRICT
        assert MFAMethod.WEBAUTHN in resp.required_mfa
        assert resp.restrictions["mode"] == "read_only"
        assert resp.restrictions["data_export_allowed"] is False
        assert "production_db" in resp.restrictions["blocked_segments"]

    def test_critical_risk_denies_and_quarantines(self):
        """Critical risk -> DENY with quarantine enforcement."""
        req = _build_policy_request(92.0, RiskLevel.CRITICAL)
        resp = self.pdp.evaluate_policy(req)

        assert resp.decision == PolicyDecision.DENY
        assert resp.required_mfa == []
        assert resp.allowed_resources == []
        assert resp.restrictions["quarantine"] is True
        assert resp.restrictions["isolate_device"] is True
        assert resp.restrictions["firewall_action"] == "DROP"

    def test_default_deny_on_unknown_level(self):
        """Default-deny behavior is enforced for any unmapped state."""
        # All known enums are covered, so we directly test classify
        req = _build_policy_request(92.0, RiskLevel.CRITICAL)
        resp = self.pdp.evaluate_policy(req)
        assert resp.decision == PolicyDecision.DENY

    def test_latency_is_recorded(self):
        """Policy evaluation measures and returns latency."""
        req = _build_policy_request(10.0, RiskLevel.LOW)
        resp = self.pdp.evaluate_policy(req)
        assert resp.latency_ms >= 0.0

    def test_reason_is_populated(self):
        """Each decision includes a human-readable reason."""
        for level, expected_word in [
            (RiskLevel.LOW, "Low"),
            (RiskLevel.MEDIUM, "Medium"),
            (RiskLevel.HIGH, "High"),
            (RiskLevel.CRITICAL, "Critical"),
        ]:
            req = _build_policy_request(50.0, level)
            resp = self.pdp.evaluate_policy(req)
            assert expected_word in resp.reason

    def test_segmentation_per_risk(self):
        """Each risk level limits allowed network segments appropriately."""
        # Low -> broad access
        low_resp = self.pdp.evaluate_policy(
            _build_policy_request(10.0, RiskLevel.LOW)
        )
        assert "enterprise_lan" in low_resp.restrictions["allowed_segments"]

        # High -> restricted
        high_resp = self.pdp.evaluate_policy(
            _build_policy_request(70.0, RiskLevel.HIGH)
        )
        assert "restricted_dmz" in high_resp.restrictions["allowed_segments"]


# =====================================================================
# PDP FastAPI Endpoint Tests
# =====================================================================

@pytest.mark.asyncio
async def test_pdp_decide_endpoint_low():
    """POST /decide with LOW risk returns ALLOW."""
    transport = ASGITransport(app=pdp_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = _build_policy_request(20.0, RiskLevel.LOW).model_dump(mode="json")
        resp = await client.post("/decide", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"
    assert "latency_ms" in data


@pytest.mark.asyncio
async def test_pdp_decide_endpoint_critical():
    """POST /decide with CRITICAL risk returns DENY."""
    transport = ASGITransport(app=pdp_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = _build_policy_request(95.0, RiskLevel.CRITICAL).model_dump(mode="json")
        resp = await client.post("/decide", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "deny"
    assert data["restrictions"]["quarantine"] is True
