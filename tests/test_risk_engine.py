"""
Unit and integration tests for the Risk Scoring Engine.

Tests:
  - Feature normalization for all 7 context features
  - Risk engine score computation and weighting
  - Threshold boundaries (Low, Medium, High, Critical)
  - Explainability output
  - FastAPI /evaluate endpoint
"""

from __future__ import annotations

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from src.common.config import RiskThresholds, RiskWeights
from src.common.models import AccessContext, DeviceInfo, RiskLevel
from src.risk_engine.app import app
from src.risk_engine.engine import RiskScoringEngine
from src.risk_engine.features import (
    normalize_behavioral_deviation,
    normalize_device_compliance,
    normalize_failed_logins,
    normalize_geo_ip,
    normalize_network_reputation,
    normalize_off_hours,
    normalize_resource_sensitivity,
)


# =====================================================================
# Feature Normalization Tests
# =====================================================================

def test_normalize_geo_ip():
    """Geo-IP normalizes properly across trusted, foreign, and blacklisted countries."""
    # Expected location
    assert normalize_geo_ip("ID") == 0.0
    # Case insensitivity
    assert normalize_geo_ip("id") == 0.0
    # Foreign / unexpected location
    assert normalize_geo_ip("US") == 0.75
    assert normalize_geo_ip("DE") == 0.75
    # High risk / blacklisted
    assert normalize_geo_ip("KP") == 1.0
    assert normalize_geo_ip("RU") == 1.0
    # Empty or unknown
    assert normalize_geo_ip("") == 1.0
    assert normalize_geo_ip("UNKNOWN") == 1.0


def test_normalize_off_hours():
    """Off-hours access distinguishes work hours, shoulders, and night/weekend."""
    # Wednesday at 10:00 (Standard work hours)
    t_work = datetime(2026, 10, 7, 10, 0)
    assert normalize_off_hours(t_work) == 0.0

    # Wednesday at 07:00 (Morning shoulder)
    t_shoulder_m = datetime(2026, 10, 7, 7, 0)
    assert normalize_off_hours(t_shoulder_m) == 0.35

    # Wednesday at 19:30 (Evening shoulder)
    t_shoulder_e = datetime(2026, 10, 7, 19, 30)
    assert normalize_off_hours(t_shoulder_e) == 0.35

    # Wednesday at 02:00 (Late night / early morning)
    t_night = datetime(2026, 10, 7, 2, 0)
    assert normalize_off_hours(t_night) == 0.85

    # Saturday at 14:00 (Weekend daytime)
    t_weekend_day = datetime(2026, 10, 10, 14, 0)
    assert normalize_off_hours(t_weekend_day) == 0.5

    # Saturday at 23:30 (Weekend night)
    t_weekend_night = datetime(2026, 10, 10, 23, 30)
    assert normalize_off_hours(t_weekend_night) == 0.9


def test_normalize_device_compliance():
    """Device compliance calculates additive penalties correctly."""
    # Fully compliant
    dev_good = DeviceInfo(
        device_id="dev-1",
        os_patched=True,
        antivirus_active=True,
        disk_encrypted=True,
        firewall_enabled=True,
    )
    assert normalize_device_compliance(dev_good) == 0.0

    # None device -> maximum penalty
    assert normalize_device_compliance(None) == 1.0

    # Missing AV only (+0.35)
    dev_no_av = DeviceInfo(
        device_id="dev-2",
        os_patched=True,
        antivirus_active=False,
        disk_encrypted=True,
        firewall_enabled=True,
    )
    assert round(normalize_device_compliance(dev_no_av), 2) == 0.35

    # Missing OS patch and Firewall (+0.35 + 0.15 = 0.50)
    dev_unpatched = DeviceInfo(
        device_id="dev-3",
        os_patched=False,
        antivirus_active=True,
        disk_encrypted=True,
        firewall_enabled=False,
    )
    assert round(normalize_device_compliance(dev_unpatched), 2) == 0.50

    # Totally non-compliant
    dev_bad = DeviceInfo(
        device_id="dev-4",
        os_patched=False,
        antivirus_active=False,
        disk_encrypted=False,
        firewall_enabled=False,
    )
    assert normalize_device_compliance(dev_bad) == 1.0


def test_normalize_failed_logins():
    """Failed login penalty escalates progressively to 1.0 at >= 5."""
    assert normalize_failed_logins(0) == 0.0
    assert normalize_failed_logins(-1) == 0.0
    assert normalize_failed_logins(1) == 0.15
    assert normalize_failed_logins(2) == 0.35
    assert normalize_failed_logins(3) == 0.65
    assert normalize_failed_logins(4) == 0.85
    assert normalize_failed_logins(5) == 1.0
    assert normalize_failed_logins(10) == 1.0


def test_normalize_network_reputation():
    """Network types map to appropriate risk rankings."""
    assert normalize_network_reputation("corporate") == 0.0
    assert normalize_network_reputation("internal") == 0.0
    assert normalize_network_reputation("vpn") == 0.20
    assert normalize_network_reputation("public") == 0.50
    assert normalize_network_reputation("proxy") == 0.80
    assert normalize_network_reputation("tor") == 1.0
    assert normalize_network_reputation("malicious") == 1.0


def test_normalize_behavioral_deviation():
    """Behavioral deviation respects [0.0, 1.0] limits."""
    assert normalize_behavioral_deviation(None) == 0.0
    assert normalize_behavioral_deviation(0.0) == 0.0
    assert normalize_behavioral_deviation(0.45) == 0.45
    assert normalize_behavioral_deviation(1.5) == 1.0
    assert normalize_behavioral_deviation(-0.5) == 0.0


def test_normalize_resource_sensitivity():
    """Resource sensitivity maps appropriately."""
    assert normalize_resource_sensitivity("low") == 0.10
    assert normalize_resource_sensitivity("normal") == 0.30
    assert normalize_resource_sensitivity("high") == 0.70
    assert normalize_resource_sensitivity("critical") == 1.0


# =====================================================================
# Engine & Threshold Classification Tests
# =====================================================================

def test_engine_threshold_classification():
    """Scores are accurately classified into Low, Medium, High, Critical."""
    engine = RiskScoringEngine(
        thresholds=RiskThresholds(low=29, medium=59, high=84, critical=100)
    )

    # Boundaries
    assert engine.classify_level(0.0) == RiskLevel.LOW
    assert engine.classify_level(29.0) == RiskLevel.LOW
    assert engine.classify_level(29.1) == RiskLevel.MEDIUM
    assert engine.classify_level(59.0) == RiskLevel.MEDIUM
    assert engine.classify_level(59.1) == RiskLevel.HIGH
    assert engine.classify_level(84.0) == RiskLevel.HIGH
    assert engine.classify_level(84.1) == RiskLevel.CRITICAL
    assert engine.classify_level(100.0) == RiskLevel.CRITICAL


def test_engine_low_risk_scenario():
    """Legitimate employee request from corporate network produces LOW risk."""
    engine = RiskScoringEngine()

    context = AccessContext(
        user_id="alice",
        device=DeviceInfo(
            device_id="laptop-1",
            os_patched=True,
            antivirus_active=True,
            disk_encrypted=True,
            firewall_enabled=True,
        ),
        source_ip="10.0.1.50",
        geo_location="ID",
        timestamp=datetime(2026, 10, 7, 10, 30),  # Wednesday 10:30
        resource_requested="/intranet/news",
        resource_sensitivity="low",
        failed_login_count=0,
        network_type="corporate",
    )

    result = engine.evaluate(context)
    assert result.level == RiskLevel.LOW
    assert result.score <= 29.0
    assert "LOW" in result.explanation


def test_engine_critical_risk_scenario():
    """Attack scenario produces CRITICAL risk (> 85)."""
    engine = RiskScoringEngine()

    context = AccessContext(
        user_id="attacker",
        device=DeviceInfo(
            device_id="unknown-dev",
            os_patched=False,
            antivirus_active=False,
            disk_encrypted=False,
            firewall_enabled=False,
        ),
        source_ip="198.51.100.2",
        geo_location="KP",  # Blacklisted
        timestamp=datetime(2026, 10, 7, 3, 0),  # 03:00 night
        resource_requested="/admin/database-dump",
        resource_sensitivity="critical",
        failed_login_count=6,  # Brute-force
        network_type="tor",
    )

    result = engine.evaluate(context)
    assert result.level == RiskLevel.CRITICAL
    assert result.score >= 85.0
    assert "CRITICAL" in result.explanation


def test_engine_explainability_content():
    """Explanation lists primary risk drivers."""
    engine = RiskScoringEngine()

    context = AccessContext(
        user_id="bob",
        device=DeviceInfo(
            device_id="bob-laptop",
            os_patched=False,
            antivirus_active=False,
            disk_encrypted=True,
            firewall_enabled=True,
        ),
        source_ip="10.0.1.51",
        geo_location="ID",
        timestamp=datetime(2026, 10, 7, 11, 0),
        resource_requested="/app/payroll",
        resource_sensitivity="high",
        failed_login_count=3,
        network_type="corporate",
    )

    result = engine.evaluate(context)
    assert "Primary risk drivers:" in result.explanation
    # Should mention highest contributor features
    assert "device_compliance" in result.explanation or "resource_sensitivity" in result.explanation


# =====================================================================
# API /evaluate Endpoint Tests
# =====================================================================

@pytest.mark.asyncio
async def test_api_evaluate_endpoint():
    """POST /evaluate returns a valid RiskScore response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "user_id": "test_user",
            "device": {
                "device_id": "test_device",
                "os_patched": True,
                "antivirus_active": True,
                "disk_encrypted": True,
                "firewall_enabled": True,
            },
            "source_ip": "192.168.1.50",
            "geo_location": "ID",
            "timestamp": "2026-10-07T11:00:00",
            "resource_requested": "/api/test",
            "resource_sensitivity": "normal",
            "failed_login_count": 0,
            "network_type": "corporate",
        }

        response = await client.post("/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "score" in data
        assert "level" in data
        assert "feature_contributions" in data
        assert "explanation" in data
        assert data["level"] == "low"
        assert len(data["feature_contributions"]) == 7
