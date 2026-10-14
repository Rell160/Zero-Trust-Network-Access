"""
Continuous Monitoring and Session Risk Re-evaluation module.

Provides active session tracking, periodic background risk re-evaluation,
adaptation triggering (step-up MFA requirement or session revocation),
and adaptation_time measurement.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Callable

from pydantic import BaseModel, Field

from src.common.logging import get_logger
from src.common.models import (
    AccessContext,
    MFAMethod,
    PolicyDecision,
    PolicyResponse,
    RiskLevel,
    RiskScore,
)

logger = get_logger("monitoring.continuous")


class ActiveSession(BaseModel):
    """Represents an active ZTNA user session."""

    session_id: str
    user_id: str
    context: AccessContext
    current_risk_score: RiskScore
    current_decision: PolicyDecision
    required_mfa: list[MFAMethod]
    is_active: bool = True
    is_quarantined: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_eval_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AdaptationEvent(BaseModel):
    """Event recorded when session risk score changes and policy adapts."""

    session_id: str
    user_id: str
    previous_level: RiskLevel
    new_level: RiskLevel
    previous_decision: PolicyDecision
    new_decision: PolicyDecision
    trigger_timestamp: float  # Unix timestamp when risk change was detected
    enforced_timestamp: float  # Unix timestamp when adaptation was applied
    adaptation_time_ms: float  # Difference in ms
    action_taken: str  # e.g., "STEP_UP_MFA", "REVOKE_SESSION", "RESTRICT_ACCESS"


class ContinuousMonitor:
    """Session tracker and risk re-evaluation engine."""

    def __init__(
        self,
        reeval_interval_seconds: float = 5.0,
        risk_evaluator: Callable[[AccessContext], RiskScore] | None = None,
        policy_evaluator: Callable[[RiskScore, AccessContext], PolicyResponse] | None = None,
    ) -> None:
        """Initialize continuous monitor.

        Args:
            reeval_interval_seconds: Polling interval for background loop.
            risk_evaluator: Function/method to compute risk score from context.
            policy_evaluator: Function/method to evaluate policy decision.
        """
        self.reeval_interval = reeval_interval_seconds
        self._risk_evaluator = risk_evaluator
        self._policy_evaluator = policy_evaluator
        self._sessions: dict[str, ActiveSession] = {}
        self._adaptation_events: list[AdaptationEvent] = []
        self._loop_task: asyncio.Task | None = None
        self._is_running = False

    def register_session(
        self,
        session_id: str,
        user_id: str,
        context: AccessContext,
        initial_risk: RiskScore,
        initial_decision: PolicyDecision,
        required_mfa: list[MFAMethod],
    ) -> ActiveSession:
        """Register a new active session for continuous monitoring."""
        session = ActiveSession(
            session_id=session_id,
            user_id=user_id,
            context=context,
            current_risk_score=initial_risk,
            current_decision=initial_decision,
            required_mfa=required_mfa,
        )
        self._sessions[session_id] = session
        logger.info(
            f"Registered session {session_id} for user {user_id}",
            extra={"extra_data": {"session_id": session_id, "user_id": user_id}},
        )
        return session

    def get_session(self, session_id: str) -> ActiveSession | None:
        """Retrieve active session by ID."""
        return self._sessions.get(session_id)

    def revoke_session(self, session_id: str, reason: str = "Explicit revocation") -> bool:
        """Revoke an active session immediately."""
        session = self._sessions.get(session_id)
        if session and session.is_active:
            session.is_active = False
            session.is_quarantined = True
            logger.info(f"Revoked session {session_id}: {reason}")
            return True
        return False

    def reevaluate_session_sync(
        self,
        session_id: str,
        updated_context: AccessContext | None = None,
    ) -> tuple[ActiveSession, AdaptationEvent | None]:
        """Synchronously re-evaluate a session's risk score and adapt policy.

        Measures Adaptation Time:
          trigger_timestamp = time when risk change was observed
          enforced_timestamp = time when new policy was applied
          adaptation_time_ms = (enforced_timestamp - trigger_timestamp) * 1000

        Args:
            session_id: ID of the session to re-evaluate.
            updated_context: Optional updated context (e.g. location changed, failed logins).

        Returns:
            Tuple of (updated ActiveSession, AdaptationEvent or None if no change).
        """
        trigger_time = time.time()

        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            raise ValueError(f"Active session {session_id} not found")

        if updated_context:
            session.context = updated_context

        # Compute new risk score
        if self._risk_evaluator:
            new_risk = self._risk_evaluator(session.context)
        else:
            # Fallback inline evaluation if no evaluator injected
            new_risk = session.current_risk_score

        prev_level = session.current_risk_score.level
        prev_decision = session.current_decision

        # Evaluate new policy decision
        if self._policy_evaluator:
            policy_resp = self._policy_evaluator(new_risk, session.context)
            new_decision = policy_resp.decision
            new_mfa = policy_resp.required_mfa
        else:
            new_decision = session.current_decision
            new_mfa = session.required_mfa

        # Check if adaptation is required
        adaptation_event: AdaptationEvent | None = None
        if new_risk.level != prev_level or new_decision != prev_decision:
            enforced_time = time.time()
            adaptation_ms = (enforced_time - trigger_time) * 1000.0

            # Determine action taken
            if new_risk.level == RiskLevel.CRITICAL:
                action = "REVOKE_AND_QUARANTINE"
                session.is_active = False
                session.is_quarantined = True
            elif new_risk.level == RiskLevel.HIGH:
                action = "RESTRICT_AND_STEP_UP_WEBAUTHN"
            elif new_risk.level == RiskLevel.MEDIUM:
                action = "STEP_UP_TOTP"
            else:
                action = "DOWNGRADE_TO_LOW_RISK"

            adaptation_event = AdaptationEvent(
                session_id=session_id,
                user_id=session.user_id,
                previous_level=prev_level,
                new_level=new_risk.level,
                previous_decision=prev_decision,
                new_decision=new_decision,
                trigger_timestamp=trigger_time,
                enforced_timestamp=enforced_time,
                adaptation_time_ms=round(adaptation_ms, 3),
                action_taken=action,
            )
            self._adaptation_events.append(adaptation_event)

            # Update session state
            session.current_risk_score = new_risk
            session.current_decision = new_decision
            session.required_mfa = new_mfa
            session.last_eval_at = datetime.now(timezone.utc)

            logger.info(
                f"Adapted session {session_id}: {prev_level.value} -> {new_risk.level.value} "
                f"in {adaptation_ms:.2f}ms. Action: {action}"
            )

        return session, adaptation_event

    def get_adaptation_events(self) -> list[AdaptationEvent]:
        """Return list of recorded adaptation events."""
        return self._adaptation_events

    def get_active_sessions_count(self) -> int:
        """Return count of currently active non-quarantined sessions."""
        return sum(1 for s in self._sessions.values() if s.is_active)
