"""
Shared Pydantic models for the ZTNA system.

These models define the data contracts between services.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk classification levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyDecision(str, Enum):
    """ZTNA policy decisions."""

    ALLOW = "allow"
    DENY = "deny"
    RESTRICT = "restrict"


class MFAMethod(str, Enum):
    """Available MFA methods."""

    NONE = "none"
    PASSWORD = "password"
    TOTP = "totp"
    WEBAUTHN = "webauthn"


class DeviceInfo(BaseModel):
    """Device compliance and identity information."""

    device_id: str
    os_patched: bool = True
    antivirus_active: bool = True
    disk_encrypted: bool = True
    firewall_enabled: bool = True


class AccessContext(BaseModel):
    """Context information for a single access request."""

    user_id: str
    device: DeviceInfo
    source_ip: str = "192.168.1.100"
    geo_location: str = "ID"  # ISO country code
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    resource_requested: str = "/api/data"
    resource_sensitivity: str = "normal"  # low, normal, high, critical
    failed_login_count: int = 0
    network_type: str = "corporate"  # corporate, vpn, public, tor
    behavioral_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Behavioral anomaly score [0.0-1.0]")


class RiskScore(BaseModel):
    """Output from the Risk Engine."""

    score: float = Field(ge=0.0, le=100.0)
    level: RiskLevel
    feature_contributions: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class PolicyRequest(BaseModel):
    """Request to the ZTNA Controller (PDP) for a policy decision."""

    user_id: str
    session_id: str = ""
    risk_score: RiskScore
    resource_requested: str
    access_context: AccessContext


class PolicyResponse(BaseModel):
    """Response from the ZTNA Controller (PDP)."""

    decision: PolicyDecision
    required_mfa: list[MFAMethod] = Field(default_factory=list)
    allowed_resources: list[str] = Field(default_factory=list)
    restrictions: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    latency_ms: float = 0.0


class HealthResponse(BaseModel):
    """Standard health check response for all services."""

    service: str
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
