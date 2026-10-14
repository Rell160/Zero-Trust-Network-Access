"""Shared pytest fixtures for the ZTNA test suite."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.risk_engine.app import app as risk_engine_app
from src.mfa_server.app import app as mfa_server_app
from src.ztna_controller.app import app as ztna_controller_app
from src.pep.app import app as pep_app


@pytest.fixture
def risk_engine_client():
    transport = ASGITransport(app=risk_engine_app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def mfa_server_client():
    transport = ASGITransport(app=mfa_server_app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def ztna_controller_client():
    transport = ASGITransport(app=ztna_controller_app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def pep_client():
    transport = ASGITransport(app=pep_app)
    return AsyncClient(transport=transport, base_url="http://test")
