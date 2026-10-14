"""Health check tests for all ZTNA services."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_risk_engine_health(risk_engine_client):
    async with risk_engine_client as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "risk-engine"
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_mfa_server_health(mfa_server_client):
    async with mfa_server_client as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mfa-server"
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ztna_controller_health(ztna_controller_client):
    async with ztna_controller_client as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ztna-controller"
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_pep_health(pep_client):
    async with pep_client as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "pep"
    assert data["status"] == "healthy"
