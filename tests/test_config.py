"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest

from src.common.config import (
    AppConfig,
    RiskThresholds,
    RiskWeights,
    get_app_config,
    load_yaml_config,
)


def test_load_yaml_config():
    config = load_yaml_config("config/config.yaml")
    assert "risk_engine" in config
    assert "mfa_server" in config


def test_load_missing_config():
    with pytest.raises(FileNotFoundError):
        load_yaml_config("nonexistent.yaml")


def test_risk_thresholds_defaults():
    t = RiskThresholds()
    assert t.low == 29
    assert t.medium == 59
    assert t.high == 84
    assert t.critical == 100


def test_risk_weights_normalized():
    w = RiskWeights()
    norm = w.normalized()
    assert abs(sum(norm.values()) - 1.0) < 1e-9


def test_get_app_config():
    config = get_app_config("config/config.yaml")
    assert isinstance(config, AppConfig)
    assert config.risk_engine.port == 8001
