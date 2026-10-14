"""
Adaptive MFA Policy Engine.

Selects appropriate authentication factors based on the evaluated RiskLevel:
  - LOW risk: Basic authentication (Password only)
  - MEDIUM risk: Step-up to TOTP (Password + TOTP)
  - HIGH risk: Strong factor (Password + WebAuthn/FIDO2 simulation)
  - CRITICAL risk: Access DENIED (no MFA prompt, quarantine device)
"""

from __future__ import annotations

from src.common.models import MFAMethod, RiskLevel


class AdaptiveMFAPolicy:
    """Evaluates risk levels to determine required authentication factors."""

    @staticmethod
    def get_required_factors(level: RiskLevel) -> list[MFAMethod]:
        """Determine required authentication factors based on risk level.

        Args:
            level: The evaluated RiskLevel (LOW, MEDIUM, HIGH, CRITICAL).

        Returns:
            List of required MFAMethod enums. Empty if access is denied.
        """
        match level:
            case RiskLevel.LOW:
                # Basic authentication only
                return [MFAMethod.PASSWORD]
            case RiskLevel.MEDIUM:
                # Step-up with Time-based One-Time Password
                return [MFAMethod.PASSWORD, MFAMethod.TOTP]
            case RiskLevel.HIGH:
                # Strong FIDO2 / WebAuthn hardware token requirement
                return [MFAMethod.PASSWORD, MFAMethod.WEBAUTHN]
            case RiskLevel.CRITICAL:
                # Direct deny - no authentication factor can satisfy
                return []
            case _:
                # Default-deny principle for unmapped risk levels
                return []

    @staticmethod
    def is_mfa_required(level: RiskLevel) -> bool:
        """Check if an additional second factor beyond password is required.

        Args:
            level: RiskLevel to inspect.

        Returns:
            True if TOTP or WebAuthn is demanded.
        """
        factors = AdaptiveMFAPolicy.get_required_factors(level)
        return any(f in (MFAMethod.TOTP, MFAMethod.WEBAUTHN) for f in factors)
