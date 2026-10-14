"""
Synthetic Traffic Generator with reproducible seed & ground truth labeling.

Generates 4 attack and legitimate scenarios:
  1. Legitimate user access (Expected country, compliant device, work hours)
  2. Credential Stuffing / Brute Force (High failed logins, rapidly changing IPs)
  3. Geo-IP Anomaly / Impossible Travel (Foreign/Blacklisted IP, off-hours)
  4. Non-compliant / Vulnerable Device Access (Unpatched OS, disabled AV/Firewall)
  5. Session Hijack simulation (Mid-session risk escalation)
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Generator

from pydantic import BaseModel, Field

from src.common.models import AccessContext, DeviceInfo


class GroundTruthRequest(BaseModel):
    """Synthetic access request bundled with ground truth research labels."""

    request_id: str
    scenario_type: str  # 'legitimate', 'credential_stuffing', 'geo_anomaly', 'non_compliant_device', 'session_hijack'
    is_malicious: bool
    expected_risk_level: str  # 'low', 'medium', 'high', 'critical'
    context: AccessContext


class SyntheticTrafficGenerator:
    """Reproducible traffic generator for experimental benchmarks."""

    def __init__(self, seed: int = 42) -> None:
        """Initialize generator with fixed seed.

        Args:
            seed: Fixed random seed for reproducibility across 30 experiment runs.
        """
        self.seed = seed
        self.reset_seed()

    def reset_seed(self) -> None:
        """Reset pseudo-random generator state to fixed seed."""
        random.seed(self.seed)

    def generate_legitimate_request(self, req_id: str) -> GroundTruthRequest:
        """Generate a legitimate access request (Expected Low/Medium risk)."""
        user_id = f"user_legit_{random.randint(1, 100)}"
        device = DeviceInfo(
            device_id=f"device_{user_id}",
            os_patched=True,
            antivirus_active=True,
            disk_encrypted=True,
            firewall_enabled=True,
        )
        context = AccessContext(
            user_id=user_id,
            device=device,
            source_ip=f"10.10.20.{random.randint(20, 200)}",
            geo_location="ID",
            timestamp=datetime(2026, 10, 7, random.randint(9, 17), random.randint(0, 59)),
            resource_requested="/api/workplace/docs",
            resource_sensitivity="normal",
            failed_login_count=0,
            network_type="corporate",
        )

        return GroundTruthRequest(
            request_id=req_id,
            scenario_type="legitimate",
            is_malicious=False,
            expected_risk_level="low",
            context=context,
        )

    def generate_credential_stuffing_request(self, req_id: str) -> GroundTruthRequest:
        """Generate a credential stuffing attack request (Expected Critical risk)."""
        user_id = f"target_user_{random.randint(1, 10)}"
        device = DeviceInfo(
            device_id=f"bot_device_{random.randint(100, 999)}",
            os_patched=random.choice([True, False]),
            antivirus_active=False,
            disk_encrypted=False,
            firewall_enabled=False,
        )
        context = AccessContext(
            user_id=user_id,
            device=device,
            source_ip=f"198.51.100.{random.randint(1, 254)}",
            geo_location="UNKNOWN",
            timestamp=datetime(2026, 10, 7, random.randint(0, 5), random.randint(0, 59)),
            resource_requested="/auth/login",
            resource_sensitivity="critical",
            failed_login_count=random.randint(5, 12),  # Brute force signature
            network_type="proxy",
        )

        return GroundTruthRequest(
            request_id=req_id,
            scenario_type="credential_stuffing",
            is_malicious=True,
            expected_risk_level="critical",
            context=context,
        )

    def generate_geo_anomaly_request(self, req_id: str) -> GroundTruthRequest:
        """Generate an impossible travel / geo anomaly request (Expected High/Critical risk)."""
        user_id = f"user_exec_{random.randint(1, 20)}"
        device = DeviceInfo(
            device_id=f"exec_laptop_{user_id}",
            os_patched=True,
            antivirus_active=True,
            disk_encrypted=True,
            firewall_enabled=True,
        )
        context = AccessContext(
            user_id=user_id,
            device=device,
            source_ip="203.0.113.88",
            geo_location=random.choice(["KP", "RU", "IR"]),  # High risk country
            timestamp=datetime(2026, 10, 7, random.randint(1, 4), random.randint(0, 59)),
            resource_requested="/finance/payroll",
            resource_sensitivity="high",
            failed_login_count=1,
            network_type="public",
        )

        return GroundTruthRequest(
            request_id=req_id,
            scenario_type="geo_anomaly",
            is_malicious=True,
            expected_risk_level="high",
            context=context,
        )

    def generate_non_compliant_device_request(self, req_id: str) -> GroundTruthRequest:
        """Generate access from a vulnerable / non-compliant device (Expected Medium/High risk)."""
        user_id = f"user_contractor_{random.randint(1, 30)}"
        device = DeviceInfo(
            device_id=f"untrusted_laptop_{user_id}",
            os_patched=False,
            antivirus_active=False,
            disk_encrypted=False,
            firewall_enabled=False,
        )
        context = AccessContext(
            user_id=user_id,
            device=device,
            source_ip=f"10.10.20.{random.randint(50, 99)}",
            geo_location="ID",
            timestamp=datetime(2026, 10, 7, random.randint(10, 16), random.randint(0, 59)),
            resource_requested="/internal/wiki",
            resource_sensitivity="normal",
            failed_login_count=0,
            network_type="cellular",
        )

        return GroundTruthRequest(
            request_id=req_id,
            scenario_type="non_compliant_device",
            is_malicious=True,  # Unauthorized posture policy violation
            expected_risk_level="high",
            context=context,
        )

    def generate_dataset(self, num_samples: int = 100) -> list[GroundTruthRequest]:
        """Generate a mixed dataset of legitimate and attack traffic requests.

        Ratio: ~60% Legitimate, ~40% Various Attack Vectors.

        Args:
            num_samples: Total number of requests to generate.

        Returns:
            List of GroundTruthRequest objects.
        """
        self.reset_seed()
        requests: list[GroundTruthRequest] = []

        generators = [
            (self.generate_legitimate_request, 0.60),
            (self.generate_credential_stuffing_request, 0.15),
            (self.generate_geo_anomaly_request, 0.15),
            (self.generate_non_compliant_device_request, 0.10),
        ]

        for i in range(num_samples):
            req_id = f"REQ-{i+1:05d}"
            r = random.random()
            cumulative = 0.0
            chosen_gen = generators[0][0]

            for gen_func, weight in generators:
                cumulative += weight
                if r <= cumulative:
                    chosen_gen = gen_func
                    break

            requests.append(chosen_gen(req_id))

        return requests
