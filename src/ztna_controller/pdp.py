"""
ZTNA Policy Decision Point (PDP) Engine.

Evaluates incoming access requests against Zero Trust principles:
  - Default Deny
  - Least Privilege
  - Risk-Aware Dynamic Access Control
  - Network segmentation and restriction mapping
"""

from __future__ import annotations

import time
from typing import Any

from src.common.config import ZTNAControllerConfig
from src.common.logging import get_logger
from src.common.models import (
    AccessContext,
    MFAMethod,
    PolicyDecision,
    PolicyRequest,
    PolicyResponse,
    RiskLevel,
    RiskScore,
)

logger = get_logger("ztna_controller.pdp")


class ZTNAPolicyDecisionPoint:
    """Core Policy Decision Point (PDP) for Zero Trust Access Control."""

    def __init__(self, config: ZTNAControllerConfig | None = None) -> None:
        """Initialize the PDP engine.

        Args:
            config: ZTNAControllerConfig configuration settings.
        """
        self.config = config or ZTNAControllerConfig()

    def evaluate_policy(self, request: PolicyRequest) -> PolicyResponse:
        """Evaluate access request and render a definitive policy decision.

        Decision Matrix:
          - LOW Risk: ALLOW
              Full access to requested resource
              Required MFA: Password only
              Restrictions: None (read/write enabled)

          - MEDIUM Risk: ALLOW (with step-up MFA condition)
              Full access to requested resource after TOTP verification
              Required MFA: Password + TOTP
              Restrictions: None (full access once authenticated)

          - HIGH Risk: RESTRICT
              Restricted access (Least privilege enforcement)
              Required MFA: Password + WebAuthn
              Restrictions: read_only=True, rate_limit=10rpm, blocked_subnets=['dmz_admin', 'db_cluster']

          - CRITICAL Risk: DENY
              Access denied immediately, quarantine triggered
              Required MFA: None (cannot satisfy)
              Restrictions: quarantine=True, isolated=True

        Args:
            request: The policy decision request containing risk score and context.

        Returns:
            PolicyResponse with decision, allowed resources, restrictions, and latency.
        """
        start_time = time.perf_counter()

        risk_level = request.risk_score.level
        resource = request.resource_requested

        decision: PolicyDecision
        required_mfa: list[MFAMethod]
        allowed_resources: list[str] = []
        restrictions: dict[str, Any] = {}
        reason: str

        match risk_level:
            case RiskLevel.LOW:
                decision = PolicyDecision.ALLOW
                required_mfa = [MFAMethod.PASSWORD]
                allowed_resources = [resource, "*"]
                restrictions = {
                    "mode": "read_write",
                    "rate_limit_per_minute": 120,
                    "session_ttl_seconds": 3600,
                    "allowed_segments": ["enterprise_lan", "internal_apps", "general_db"],
                }
                reason = "Low risk profile: Full access granted under basic authentication."

            case RiskLevel.MEDIUM:
                decision = PolicyDecision.ALLOW
                required_mfa = [MFAMethod.PASSWORD, MFAMethod.TOTP]
                allowed_resources = [resource]
                restrictions = {
                    "mode": "read_write",
                    "rate_limit_per_minute": 60,
                    "session_ttl_seconds": 1800,
                    "allowed_segments": ["enterprise_lan", "internal_apps"],
                }
                reason = "Medium risk profile: Access granted subject to TOTP verification."

            case RiskLevel.HIGH:
                decision = PolicyDecision.RESTRICT
                required_mfa = [MFAMethod.PASSWORD, MFAMethod.WEBAUTHN]
                allowed_resources = [resource]
                restrictions = {
                    "mode": "read_only",
                    "rate_limit_per_minute": 15,
                    "session_ttl_seconds": 600,
                    "allowed_segments": ["restricted_dmz"],
                    "blocked_segments": ["production_db", "admin_portal", "core_network"],
                    "data_export_allowed": False,
                }
                reason = "High risk profile: Restricted read-only access with FIDO2 MFA requirement."

            case RiskLevel.CRITICAL:
                decision = PolicyDecision.DENY
                required_mfa = []
                allowed_resources = []
                restrictions = {
                    "quarantine": True,
                    "isolate_device": True,
                    "revoke_active_sessions": True,
                    "firewall_action": "DROP",
                }
                reason = "Critical risk profile: Access denied and device quarantine initiated."

            case _:
                # Default Deny principle
                decision = PolicyDecision.DENY
                required_mfa = []
                allowed_resources = []
                restrictions = {"reason": "Unrecognized risk level, default-deny enforced"}
                reason = "Default Deny: Unrecognized risk state."

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return PolicyResponse(
            decision=decision,
            required_mfa=required_mfa,
            allowed_resources=allowed_resources,
            restrictions=restrictions,
            reason=reason,
            latency_ms=round(elapsed_ms, 3),
        )
