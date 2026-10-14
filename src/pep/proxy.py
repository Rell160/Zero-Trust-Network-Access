"""
Policy Enforcement Point (PEP) Proxy implementation.

Acts as a reverse proxy gateway sitting in front of protected enterprise resources:
  1. Intercepts all incoming client requests.
  2. Forwards request context to Risk Engine (POST /evaluate).
  3. Queries ZTNA Controller PDP (POST /decide) with computed risk.
  4. Enforces Adaptive MFA if required by PDP.
  5. Enforces Dynamic Access Controls (Allow, Deny, Restrict read-only).
  6. Proxies legitimate traffic to upstream services.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from src.common.config import PEPConfig
from src.common.logging import get_logger
from src.common.models import (
    AccessContext,
    MFAMethod,
    PolicyDecision,
    PolicyRequest,
    PolicyResponse,
    RiskScore,
)

logger = get_logger("pep.proxy")


class PolicyEnforcementPoint:
    """Enforces PDP decisions and manages reverse-proxying."""

    def __init__(
        self,
        config: PEPConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize PEP proxy.

        Args:
            config: PEPConfig configuration parameters.
            http_client: Async HTTP client for communicating with microservices.
        """
        self.config = config or PEPConfig()
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def evaluate_risk(self, context: AccessContext) -> RiskScore:
        """Call Risk Engine service to evaluate request risk."""
        client = await self._get_client()
        url = f"{self.config.risk_engine_url}/evaluate"
        # In memory/dev mode fallback handled gracefully
        resp = await client.post(url, json=context.model_dump(mode="json"))
        resp.raise_for_status()
        return RiskScore(**resp.json())

    async def request_policy_decision(
        self,
        user_id: str,
        session_id: str,
        risk_score: RiskScore,
        resource_requested: str,
        context: AccessContext,
    ) -> PolicyResponse:
        """Call ZTNA Controller PDP to obtain policy decision."""
        client = await self._get_client()
        url = f"{self.config.controller_url}/decide"

        policy_req = PolicyRequest(
            user_id=user_id,
            session_id=session_id,
            risk_score=risk_score,
            resource_requested=resource_requested,
            access_context=context,
        )

        resp = await client.post(url, json=policy_req.model_dump(mode="json"))
        resp.raise_for_status()
        return PolicyResponse(**resp.json())

    async def enforce(
        self,
        context: AccessContext,
        session_id: str = "",
        mfa_verified: bool = False,
        mfa_method_used: MFAMethod = MFAMethod.NONE,
    ) -> dict[str, Any]:
        """Complete PEP enforcement pipeline for an incoming access request.

        Pipeline:
          Context -> Risk Engine -> PDP Decision -> MFA Check -> Access Control

        Args:
            context: Access context from client request.
            session_id: Client session identifier.
            mfa_verified: Whether the client has already satisfied required MFA.
            mfa_method_used: MFA method verified by client.

        Returns:
            Dictionary with decision status, HTTP status code, restrictions, and proxy info.
        """
        start_time = time.perf_counter()

        # Step 1: Risk Engine Evaluation
        try:
            risk_score = await self.evaluate_risk(context)
        except Exception as e:
            logger.error(f"Failed to reach Risk Engine, enforcing default deny: {e}")
            return {
                "status": "denied",
                "http_status": 503,
                "reason": "Risk evaluation service unavailable - Default Deny enforced",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3),
            }

        # Step 2: PDP Policy Decision
        try:
            pdp_response = await self.request_policy_decision(
                user_id=context.user_id,
                session_id=session_id,
                risk_score=risk_score,
                resource_requested=context.resource_requested,
                context=context,
            )
        except Exception as e:
            logger.error(f"Failed to reach ZTNA Controller, enforcing default deny: {e}")
            return {
                "status": "denied",
                "http_status": 503,
                "reason": "ZTNA Controller PDP unavailable - Default Deny enforced",
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 3),
            }

        # Step 3: Enforce Decision Matrix
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        if pdp_response.decision == PolicyDecision.DENY:
            return {
                "status": "denied",
                "http_status": 403,
                "decision": pdp_response.decision.value,
                "risk_score": risk_score.score,
                "risk_level": risk_score.level.value,
                "reason": pdp_response.reason,
                "quarantine": pdp_response.restrictions.get("quarantine", False),
                "latency_ms": elapsed_ms,
            }

        # Step 4: MFA Verification Enforcement
        requires_mfa = any(
            f in (MFAMethod.TOTP, MFAMethod.WEBAUTHN) for f in pdp_response.required_mfa
        )

        if requires_mfa and not mfa_verified:
            return {
                "status": "mfa_required",
                "http_status": 401,
                "decision": pdp_response.decision.value,
                "risk_score": risk_score.score,
                "risk_level": risk_score.level.value,
                "required_mfa": [f.value for f in pdp_response.required_mfa],
                "reason": "Additional MFA verification required before access is granted.",
                "latency_ms": elapsed_ms,
            }

        # Step 5: Access Granted (Full or Restricted)
        is_restricted = pdp_response.decision == PolicyDecision.RESTRICT

        return {
            "status": "allowed",
            "http_status": 200,
            "decision": pdp_response.decision.value,
            "risk_score": risk_score.score,
            "risk_level": risk_score.level.value,
            "restricted": is_restricted,
            "restrictions": pdp_response.restrictions,
            "allowed_resources": pdp_response.allowed_resources,
            "upstream_target": self.config.target_upstream_url,
            "latency_ms": elapsed_ms,
        }
