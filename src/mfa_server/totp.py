"""
Time-Based One-Time Password (TOTP) logic.

Wraps the pyotp library for standard RFC 6238 TOTP validation.
"""

from __future__ import annotations

import pyotp

from src.common.config import MFAServerConfig
from src.mfa_server.store import MFAStore


class TOTPManager:
    """Manages TOTP secret generation, URIs, and code verification."""

    def __init__(self, store: MFAStore, config: MFAServerConfig) -> None:
        """Initialize TOTP manager.

        Args:
            store: Persistent storage reference.
            config: MFA Server configuration (issuer, digits, interval).
        """
        self.store = store
        self.config = config

    def generate_secret(self) -> str:
        """Generate a random base32 encoded TOTP secret."""
        return pyotp.random_base32()

    def generate_provisioning_uri(
        self, user_id: str, secret: str, account_name: str | None = None
    ) -> str:
        """Generate an otpauth:// URI for QR code enrollment.

        Args:
            user_id: User identifier.
            secret: Base32 TOTP secret.
            account_name: Optional display name (defaults to user_id).

        Returns:
            Provisioning URI string.
        """
        name = account_name or user_id
        totp = pyotp.TOTP(
            secret,
            digits=self.config.totp_digits,
            interval=self.config.totp_interval_seconds,
        )
        return totp.provisioning_uri(name=name, issuer_name=self.config.issuer_name)

    def enroll(self, user_id: str) -> tuple[str, str]:
        """Enroll a user with a new TOTP secret.

        Args:
            user_id: The user to enroll.

        Returns:
            Tuple of (secret_base32, provisioning_uri).
        """
        secret = self.generate_secret()
        self.store.save_totp_secret(user_id, secret)
        uri = self.generate_provisioning_uri(user_id, secret)
        return secret, uri

    def verify(self, user_id: str, code: str) -> bool:
        """Verify a 6-digit TOTP code against the user's secret.

        Args:
            user_id: The user attempting verification.
            code: The 6-digit TOTP string provided by the user.

        Returns:
            True if valid, False otherwise (or if user has no secret).
        """
        secret = self.store.get_totp_secret(user_id)
        if not secret:
            return False

        totp = pyotp.TOTP(
            secret,
            digits=self.config.totp_digits,
            interval=self.config.totp_interval_seconds,
        )

        # Allow 1 window of skew (±30s) to account for clock drift
        return totp.verify(code, valid_window=1)
