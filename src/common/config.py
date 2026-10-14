"""
Configuration loader for the ZTNA system.

Loads settings from config/config.yaml and environment variables.
Environment variables take precedence over YAML values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def load_yaml_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config YAML. Defaults to CONFIG_PATH env var
                     or config/config.yaml.

    Returns:
        Parsed YAML configuration dictionary.
    """
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config/config.yaml")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class RiskThresholds(BaseModel):
    """Risk score threshold boundaries."""

    low: int = Field(default=29, ge=0, le=100, description="Upper bound for Low risk")
    medium: int = Field(default=59, ge=0, le=100, description="Upper bound for Medium risk")
    high: int = Field(default=84, ge=0, le=100, description="Upper bound for High risk")
    critical: int = Field(default=100, ge=0, le=100, description="Upper bound for Critical risk")


class RiskWeights(BaseModel):
    """Feature weights for risk scoring. Should sum to 1.0."""

    geo_ip_anomaly: float = Field(default=0.15, ge=0.0, le=1.0)
    off_hours_access: float = Field(default=0.10, ge=0.0, le=1.0)
    device_compliance: float = Field(default=0.20, ge=0.0, le=1.0)
    failed_login_attempts: float = Field(default=0.15, ge=0.0, le=1.0)
    network_reputation: float = Field(default=0.15, ge=0.0, le=1.0)
    behavioral_deviation: float = Field(default=0.10, ge=0.0, le=1.0)
    resource_sensitivity: float = Field(default=0.15, ge=0.0, le=1.0)

    def normalized(self) -> dict[str, float]:
        """Return weights normalized to sum to 1.0."""
        values = self.model_dump()
        total = sum(values.values())
        if total == 0:
            return values
        return {k: v / total for k, v in values.items()}


class RiskEngineConfig(BaseModel):
    """Risk Engine service configuration."""

    host: str = "0.0.0.0"
    port: int = 8001
    thresholds: RiskThresholds = RiskThresholds()
    weights: RiskWeights = RiskWeights()


class MFAServerConfig(BaseModel):
    """MFA Server service configuration."""

    host: str = "0.0.0.0"
    port: int = 8002
    issuer_name: str = "ZTNA-Enterprise"
    totp_digits: int = 6
    totp_interval_seconds: int = 30


class ZTNAControllerConfig(BaseModel):
    """ZTNA Controller (PDP) configuration."""

    host: str = "0.0.0.0"
    port: int = 8003
    default_policy: str = "DENY"
    session_timeout_seconds: int = 3600
    continuous_reeval_interval_seconds: int = 30


class PEPConfig(BaseModel):
    """Policy Enforcement Point configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    target_upstream_url: str = "http://enterprise-vm-stub:8080"
    controller_url: str = "http://ztna-controller:8003"
    risk_engine_url: str = "http://risk-engine:8001"
    mfa_server_url: str = "http://mfa-server:8002"


class AppConfig(BaseModel):
    """Root application configuration."""

    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    risk_engine: RiskEngineConfig = RiskEngineConfig()
    mfa_server: MFAServerConfig = MFAServerConfig()
    ztna_controller: ZTNAControllerConfig = ZTNAControllerConfig()
    pep: PEPConfig = PEPConfig()


def get_app_config(config_path: str | None = None) -> AppConfig:
    """Load and return typed application configuration.

    Args:
        config_path: Path to config YAML file.

    Returns:
        AppConfig instance with validated settings.
    """
    raw = load_yaml_config(config_path)

    # Flatten: merge top-level 'app' keys into sub-configs
    app_section = raw.get("app", {})
    return AppConfig(
        env=app_section.get("env", "development"),
        debug=app_section.get("debug", True),
        log_level=app_section.get("log_level", "INFO"),
        risk_engine=RiskEngineConfig(**raw.get("risk_engine", {})),
        mfa_server=MFAServerConfig(**raw.get("mfa_server", {})),
        ztna_controller=ZTNAControllerConfig(**raw.get("ztna_controller", {})),
        pep=PEPConfig(**raw.get("pep", {})),
    )
