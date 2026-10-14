"""
Unit and integration tests for Continuous Monitoring & Risk Re-evaluation.

Tests:
  - Session lifecycle (registration, active lookup, revocation)
  - Risk re-evaluation and policy adaptation triggering
  - Step-up MFA triggers on risk escalation (LOW -> MEDIUM / HIGH)
  - Session revocation and quarantine on CRITICAL escalation
  - Adaptation time calculation (variable 10)
"""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from src.common.models import (
    AccessContext,
    DeviceInfo,
    MFAMethod,
    PolicyDecision,
    PolicyRequest,
    PolicyResponse,
    RiskLevel,
    RiskScore,
)
from src.monitoring.continuous import (
    ActiveSession,
    AdaptationEvent,
    ContinuousMonitor,
)
from src.risk_engine.engine import RiskScoringEngine
from src.ztna_controller.pdp import ZTNAPolicyDecisionPoint


@pytest.fixture
def risk_engine() -> RiskScoringEngine:
    return RiskScoringEngine()


@pytest.fixture
def pdp_engine() -> ZTNAPolicyDecisionPoint:
    return ZTNAPolicyDecisionPoint()


@pytest.fixture
def monitor(risk_engine, pdp_engine) -> ContinuousMonitor:
    def risk_eval(ctx: AccessContext) -> RiskScore:
        return risk_engine.evaluate(ctx)

    def policy_eval(risk: RiskScore, ctx: AccessContext) -> PolicyResponse:
        req = PolicyRequest(
            user_id=ctx.user_id,
            session_id="test-sess",
            risk_score=risk,
            resource_requested=ctx.resource_requested,
            access_context=ctx,
        )
        return pdp_engine.evaluate_policy(req)

    return ContinuousMonitor(
        reeval_interval_seconds=1.0,
        risk_evaluator=risk_eval,
        policy_evaluator=policy_eval,
    )


class TestContinuousMonitoring:
    """Test suite for continuous session risk re-evaluation."""

    def test_session_registration_and_lookup(self, monitor):
        """Monitor registers active sessions correctly."""
        ctx = AccessContext(
            user_id="alice",
            device=DeviceInfo(device_id="laptop-1"),
            resource_requested="/api/data",
        )
        initial_risk = RiskScore(
            score=10.0,
            level=RiskLevel.LOW,
            feature_contributions={},
            explanation="Initial low risk",
        )

        session = monitor.register_session(
            session_id="sess-001",
            user_id="alice",
            context=ctx,
            initial_risk=initial_risk,
            initial_decision=PolicyDecision.ALLOW,
            required_mfa=[MFAMethod.PASSWORD],
        )

        assert session.session_id == "sess-001"
        assert session.is_active is True
        assert monitor.get_active_sessions_count() == 1
        assert monitor.get_session("sess-001") is not None

    def test_risk_escalation_triggers_mfa_stepup(self, monitor):
        """When risk increases to MEDIUM/HIGH, step-up MFA adaptation is recorded."""
        ctx_initial = AccessContext(
            user_id="bob",
            device=DeviceInfo(device_id="laptop-2"),
            source_ip="10.0.1.50",
            geo_location="ID",
            network_type="corporate",
            failed_login_count=0,
            resource_sensitivity="low",
        )
        initial_risk = RiskScore(
            score=5.0,
            level=RiskLevel.LOW,
            feature_contributions={},
            explanation="Initial",
        )

        monitor.register_session(
            session_id="sess-002",
            user_id="bob",
            context=ctx_initial,
            initial_risk=initial_risk,
            initial_decision=PolicyDecision.ALLOW,
            required_mfa=[MFAMethod.PASSWORD],
        )

        # Context updates to Medium/High: Foreign IP + failed logins + non-compliant AV
        ctx_escalated = AccessContext(
            user_id="bob",
            device=DeviceInfo(
                device_id="laptop-2",
                antivirus_active=False,
                os_patched=True,
                disk_encrypted=True,
                firewall_enabled=True,
            ),
            source_ip="198.51.100.5",
            geo_location="US",  # Anomaly
            network_type="public",
            failed_login_count=3,
            resource_sensitivity="high",
            timestamp=datetime(2026, 10, 7, 23, 0),  # Late night
        )

        session, event = monitor.reevaluate_session_sync(
            session_id="sess-002", updated_context=ctx_escalated
        )

        assert event is not None
        assert event.previous_level == RiskLevel.LOW
        assert event.new_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
        assert event.adaptation_time_ms >= 0.0
        assert "STEP_UP" in event.action_taken

    def test_critical_risk_escalation_quarantines_session(self, monitor):
        """When risk escalates to CRITICAL, session is revoked and quarantined."""
        ctx_initial = AccessContext(
            user_id="charlie",
            device=DeviceInfo(device_id="laptop-3"),
            source_ip="10.0.1.52",
            geo_location="ID",
            network_type="corporate",
        )
        initial_risk = RiskScore(
            score=5.0,
            level=RiskLevel.LOW,
            feature_contributions={},
            explanation="Initial",
        )

        monitor.register_session(
            session_id="sess-003",
            user_id="charlie",
            context=ctx_initial,
            initial_risk=initial_risk,
            initial_decision=PolicyDecision.ALLOW,
            required_mfa=[MFAMethod.PASSWORD],
        )

        # Context updates to critical: Blacklisted Geo + Tor + totally noncompliant + brute force
        ctx_critical = AccessContext(
            user_id="charlie",
            device=DeviceInfo(
                device_id="laptop-3",
                os_patched=False,
                antivirus_active=False,
                disk_encrypted=False,
                firewall_enabled=False,
            ),
            source_ip="198.51.100.10",
            geo_location="KP",
            network_type="tor",
            failed_login_count=6,
            resource_sensitivity="critical",
            timestamp=datetime(2026, 10, 7, 3, 0),
        )

        session, event = monitor.reevaluate_session_sync(
            session_id="sess-003", updated_context=ctx_critical
        )

        assert event is not None
        assert event.new_level == RiskLevel.CRITICAL
        assert event.action_taken == "REVOKE_AND_QUARANTINE"
        assert session.is_active is False
        assert session.is_quarantined is True
        assert monitor.get_active_sessions_count() == 0

    def test_adaptation_time_is_measured(self, monitor):
        """Adaptation time (variable 10) is measured accurately in milliseconds."""
        ctx = AccessContext(
            user_id="dave",
            device=DeviceInfo(device_id="laptop-4"),
            resource_sensitivity="low",
            geo_location="ID",
        )
        initial_risk = RiskScore(
            score=10.0,
            level=RiskLevel.LOW,
            feature_contributions={},
            explanation="Low",
        )

        monitor.register_session(
            session_id="sess-004",
            user_id="dave",
            context=ctx,
            initial_risk=initial_risk,
            initial_decision=PolicyDecision.ALLOW,
            required_mfa=[MFAMethod.PASSWORD],
        )

        # Update context to High Risk
        ctx_updated = AccessContext(
            user_id="dave",
            device=DeviceInfo(
                device_id="laptop-4",
                os_patched=False,
                antivirus_active=False,
            ),
            geo_location="US",
            failed_login_count=4,
            network_type="public",
            resource_sensitivity="high",
            timestamp=datetime(2026, 10, 7, 23, 30),
        )

        session, event = monitor.reevaluate_session_sync(
            session_id="sess-004", updated_context=ctx_updated
        )

        assert event is not None
        assert isinstance(event.adaptation_time_ms, float)
        assert event.adaptation_time_ms >= 0.0
        assert len(monitor.get_adaptation_events()) >= 1
