"""
Context feature extraction and normalization for the Risk Engine.

All features are normalized to the [0.0, 1.0] interval:
  0.0 = minimal / no risk
  1.0 = maximum / critical risk
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from src.common.models import AccessContext, DeviceInfo


def normalize_geo_ip(
    geo_location: str,
    expected_locations: set[str] | None = None,
    high_risk_locations: set[str] | None = None,
) -> float:
    """Normalize Geo-IP location anomaly score.

    Args:
        geo_location: 2-letter ISO country code (e.g., 'ID', 'US', 'RU').
        expected_locations: Set of legitimate country codes. Defaults to {'ID'}.
        high_risk_locations: Set of known high-risk origin countries.

    Returns:
        Float in [0.0, 1.0].
    """
    if expected_locations is None:
        expected_locations = {"ID"}
    if high_risk_locations is None:
        high_risk_locations = {"KP", "IR", "SY", "RU", "UNKNOWN", "TOR"}

    loc_upper = (geo_location or "").strip().upper()

    if not loc_upper or loc_upper in high_risk_locations:
        return 1.0

    if loc_upper in expected_locations:
        return 0.0

    # Foreign country but not explicitly blacklisted
    return 0.75


def normalize_off_hours(access_time: datetime | None = None) -> float:
    """Normalize access time relative to standard business hours.

    Standard business hours: Mon-Fri, 08:00 - 18:00 local time.
    Off-hours: Night (22:00 - 06:00), Weekends (Sat-Sun).

    Args:
        access_time: Datetime of request. Defaults to current local time.

    Returns:
        Float in [0.0, 1.0].
    """
    if access_time is None:
        access_time = datetime.now()

    # Weekend check (5 = Saturday, 6 = Sunday)
    is_weekend = access_time.weekday() >= 5
    hour = access_time.hour + (access_time.minute / 60.0)

    if is_weekend:
        # Weekend daytime: 0.5, Weekend late night: 0.9
        if 8.0 <= hour <= 20.0:
            return 0.5
        return 0.9

    # Weekday rules
    if 8.0 <= hour < 18.0:
        # Standard work hours
        return 0.0
    elif (6.0 <= hour < 8.0) or (18.0 <= hour < 22.0):
        # Shoulder / transition hours
        return 0.35
    else:
        # Late night / early morning (22:00 - 06:00)
        return 0.85


def normalize_device_compliance(device: DeviceInfo | None) -> float:
    """Normalize device posture and compliance score.

    Calculates penalty based on missing security controls:
      - OS not patched: +0.35 penalty
      - Antivirus inactive: +0.35 penalty
      - Disk not encrypted: +0.15 penalty
      - Firewall disabled: +0.15 penalty

    Args:
        device: Device posture details.

    Returns:
        Float in [0.0, 1.0]. 0.0 = fully compliant, 1.0 = non-compliant.
    """
    if device is None:
        return 1.0

    penalty = 0.0
    if not device.os_patched:
        penalty += 0.35
    if not device.antivirus_active:
        penalty += 0.35
    if not device.disk_encrypted:
        penalty += 0.15
    if not device.firewall_enabled:
        penalty += 0.15

    return min(1.0, penalty)


def normalize_failed_logins(failed_count: int) -> float:
    """Normalize consecutive failed login attempts.

    Step-function / progressive penalty:
      0 fails: 0.0
      1 fail:  0.15
      2 fails: 0.35
      3 fails: 0.65
      4 fails: 0.85
      >= 5 fails: 1.0 (brute force signature)

    Args:
        failed_count: Number of consecutive failed logins.

    Returns:
        Float in [0.0, 1.0].
    """
    if failed_count <= 0:
        return 0.0
    elif failed_count == 1:
        return 0.15
    elif failed_count == 2:
        return 0.35
    elif failed_count == 3:
        return 0.65
    elif failed_count == 4:
        return 0.85
    else:
        return 1.0


def normalize_network_reputation(network_type: str) -> float:
    """Normalize network origin and reputation.

    Risk ranking by network type:
      - corporate / internal: 0.0
      - enterprise_vpn / vpn: 0.20
      - public / cellular / home: 0.50
      - proxy / hosting: 0.80
      - tor / malicious: 1.0

    Args:
        network_type: Identifier of the network origin.

    Returns:
        Float in [0.0, 1.0].
    """
    net = (network_type or "").strip().lower()

    mapping = {
        "corporate": 0.0,
        "internal": 0.0,
        "lan": 0.0,
        "vpn": 0.20,
        "enterprise_vpn": 0.20,
        "public": 0.50,
        "cellular": 0.50,
        "home": 0.50,
        "proxy": 0.80,
        "hosting": 0.80,
        "tor": 1.0,
        "malicious": 1.0,
    }

    return mapping.get(net, 0.70)


def normalize_behavioral_deviation(deviation_score: float | None = None) -> float:
    """Normalize behavioral anomaly deviation score.

    Args:
        deviation_score: Raw deviation score if provided (0.0 - 1.0).

    Returns:
        Float in [0.0, 1.0].
    """
    if deviation_score is None:
        return 0.0
    return max(0.0, min(1.0, float(deviation_score)))


def normalize_resource_sensitivity(sensitivity: str | Literal["low", "normal", "high", "critical"]) -> float:
    """Normalize requested resource classification level.

    Sensitivity levels:
      - low (public intranet, general wiki): 0.10
      - normal (daily workplace docs, internal tools): 0.30
      - high (financial records, code repositories): 0.70
      - critical (production credentials, DB console, admin access): 1.0

    Args:
        sensitivity: Sensitivity label.

    Returns:
        Float in [0.0, 1.0].
    """
    sens = (sensitivity or "normal").strip().lower()

    mapping = {
        "low": 0.10,
        "normal": 0.30,
        "high": 0.70,
        "critical": 1.0,
    }

    return mapping.get(sens, 0.50)


def extract_all_features(context: AccessContext) -> dict[str, float]:
    """Extract and normalize all 7 context features from an AccessContext.

    Args:
        context: The incoming access context.

    Returns:
        Dictionary mapping feature names to normalized scores in [0.0, 1.0].
    """
    return {
        "geo_ip_anomaly": normalize_geo_ip(context.geo_location),
        "off_hours_access": normalize_off_hours(context.timestamp),
        "device_compliance": normalize_device_compliance(context.device),
        "failed_login_attempts": normalize_failed_logins(context.failed_login_count),
        "network_reputation": normalize_network_reputation(context.network_type),
        "behavioral_deviation": normalize_behavioral_deviation(
            getattr(context, "behavioral_score", 0.0)
        ),
        "resource_sensitivity": normalize_resource_sensitivity(context.resource_sensitivity),
    }
