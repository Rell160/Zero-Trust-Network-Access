"""
In-memory store for MFA Server.

Stores TOTP secrets and WebAuthn challenge state keyed by user_id.
In production, this would be backed by an encrypted database (PostgreSQL/Redis).
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TOTPRecord:
    """Stored TOTP enrollment for a user."""

    user_id: str
    secret: str
    enrolled_at: float = field(default_factory=time.time)


@dataclass
class WebAuthnChallenge:
    """Stored WebAuthn challenge awaiting verification."""

    user_id: str
    challenge: str           # Random challenge bytes hex-encoded
    credential_id: str       # Simulated credential identifier
    public_key_hex: str      # Simulated ECDSA-like public key (32 random bytes)
    expires_at: float        # Unix timestamp of expiry


class MFAStore:
    """Thread-safe (single-process) in-memory MFA state store."""

    def __init__(self, challenge_ttl_seconds: int = 60) -> None:
        """Initialize empty stores.

        Args:
            challenge_ttl_seconds: How long a WebAuthn challenge is valid.
        """
        self._challenge_ttl = challenge_ttl_seconds
        self._totp_records: dict[str, TOTPRecord] = {}
        self._webauthn_challenges: dict[str, WebAuthnChallenge] = {}
        self._webauthn_credentials: dict[str, str] = {}  # user_id -> credential_id

    # ------------------------------------------------------------------ TOTP
    def save_totp_secret(self, user_id: str, secret: str) -> None:
        """Persist a TOTP secret for a user (overwrites existing)."""
        self._totp_records[user_id] = TOTPRecord(user_id=user_id, secret=secret)

    def get_totp_secret(self, user_id: str) -> Optional[str]:
        """Retrieve TOTP secret for a user, or None if not enrolled."""
        record = self._totp_records.get(user_id)
        return record.secret if record else None

    def has_totp(self, user_id: str) -> bool:
        """Return True if user has a TOTP enrollment."""
        return user_id in self._totp_records

    # -------------------------------------------------------------- WebAuthn
    def save_webauthn_challenge(
        self,
        user_id: str,
        challenge: str,
        credential_id: str,
        public_key_hex: str,
    ) -> None:
        """Store a pending WebAuthn challenge for a user."""
        self._webauthn_challenges[user_id] = WebAuthnChallenge(
            user_id=user_id,
            challenge=challenge,
            credential_id=credential_id,
            public_key_hex=public_key_hex,
            expires_at=time.time() + self._challenge_ttl,
        )

    def get_webauthn_challenge(self, user_id: str) -> Optional[WebAuthnChallenge]:
        """Retrieve a non-expired challenge, or None."""
        ch = self._webauthn_challenges.get(user_id)
        if ch is None:
            return None
        if time.time() > ch.expires_at:
            del self._webauthn_challenges[user_id]
            return None
        return ch

    def consume_webauthn_challenge(self, user_id: str) -> Optional[WebAuthnChallenge]:
        """Get and delete challenge (one-shot use)."""
        ch = self.get_webauthn_challenge(user_id)
        if ch:
            self._webauthn_challenges.pop(user_id, None)
        return ch

    def save_webauthn_credential(self, user_id: str, credential_id: str) -> None:
        """Register a WebAuthn credential ID for a user."""
        self._webauthn_credentials[user_id] = credential_id

    def get_webauthn_credential_id(self, user_id: str) -> Optional[str]:
        """Return registered credential_id or None."""
        return self._webauthn_credentials.get(user_id)

    def has_webauthn(self, user_id: str) -> bool:
        """Return True if user has a registered WebAuthn credential."""
        return user_id in self._webauthn_credentials

    def generate_challenge(self) -> str:
        """Generate a secure random challenge (32 bytes hex)."""
        return secrets.token_hex(32)

    def generate_credential_id(self) -> str:
        """Generate a random credential ID."""
        return secrets.token_urlsafe(20)

    def generate_public_key(self) -> str:
        """Generate a simulated public key (32 random bytes hex)."""
        return secrets.token_hex(32)
