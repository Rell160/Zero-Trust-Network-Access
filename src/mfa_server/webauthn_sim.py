"""
WebAuthn/FIDO2 Strong Authentication Simulation.

Simulates WebAuthn registration and authentication flows using HMAC-SHA256
as a cryptographic stand-in for ECDSA keypair signatures.

Flow:
  1. Server issues a challenge (random hex string) & credential_id.
  2. Client computes assertion signature: HMAC-SHA256(challenge, public_key).
  3. Server verifies signature matching the challenge stored in MFAStore.
"""

from __future__ import annotations

import hmac
import hashlib

from src.mfa_server.store import MFAStore, WebAuthnChallenge


class WebAuthnSimulator:
    """Cryptographic simulator for WebAuthn / FIDO2 strong MFA."""

    def __init__(self, store: MFAStore) -> None:
        """Initialize simulator.

        Args:
            store: MFAStore reference for challenge/credential persistence.
        """
        self.store = store

    @staticmethod
    def compute_signature(challenge: str, public_key_hex: str) -> str:
        """Compute expected assertion signature for a given challenge & key.

        Computes HMAC-SHA256(key=public_key_hex, msg=challenge).

        Args:
            challenge: Hex challenge string issued by server.
            public_key_hex: Simulated public key hex string.

        Returns:
            Hex-encoded signature string.
        """
        key_bytes = bytes.fromhex(public_key_hex)
        msg_bytes = challenge.encode("utf-8")
        return hmac.new(key_bytes, msg_bytes, hashlib.sha256).hexdigest()

    def begin_registration(self, user_id: str) -> dict[str, str]:
        """Begin WebAuthn credential registration for a user.

        Args:
            user_id: User identifier.

        Returns:
            Dictionary with challenge, credential_id, and simulated public_key_hex.
        """
        challenge = self.store.generate_challenge()
        credential_id = self.store.generate_credential_id()
        public_key = self.store.generate_public_key()

        self.store.save_webauthn_challenge(
            user_id=user_id,
            challenge=challenge,
            credential_id=credential_id,
            public_key_hex=public_key,
        )

        return {
            "user_id": user_id,
            "challenge": challenge,
            "credential_id": credential_id,
            "public_key_hex": public_key,
        }

    def finish_registration(
        self, user_id: str, signature: str
    ) -> bool:
        """Finish registration by verifying signature over challenge.

        Args:
            user_id: User identifier.
            signature: Signature computed by authenticator client.

        Returns:
            True if registration signature is valid, False otherwise.
        """
        ch = self.store.consume_webauthn_challenge(user_id)
        if ch is None:
            return False

        expected = self.compute_signature(ch.challenge, ch.public_key_hex)
        if hmac.compare_digest(signature, expected):
            self.store.save_webauthn_credential(user_id, ch.credential_id)
            return True
        return False

    def begin_assertion(self, user_id: str) -> dict[str, str] | None:
        """Begin WebAuthn authentication assertion flow.

        Args:
            user_id: User identifier.

        Returns:
            Dict containing challenge & credential_id, or None if not enrolled.
        """
        if not self.store.has_webauthn(user_id):
            return None

        ch_hex = self.store.generate_challenge()
        cred_id = self.store.get_webauthn_credential_id(user_id) or "cred-unknown"
        pub_key = self.store.generate_public_key()  # Key bound to session

        self.store.save_webauthn_challenge(
            user_id=user_id,
            challenge=ch_hex,
            credential_id=cred_id,
            public_key_hex=pub_key,
        )

        return {
            "user_id": user_id,
            "challenge": ch_hex,
            "credential_id": cred_id,
            "public_key_hex": pub_key,
        }

    def finish_assertion(self, user_id: str, signature: str) -> bool:
        """Finish assertion by verifying response signature.

        Args:
            user_id: User identifier.
            signature: Client's computed assertion signature.

        Returns:
            True if signature matches pending challenge, False otherwise.
        """
        ch = self.store.consume_webauthn_challenge(user_id)
        if ch is None:
            return False

        expected = self.compute_signature(ch.challenge, ch.public_key_hex)
        return hmac.compare_digest(signature, expected)
