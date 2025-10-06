"""Tests for FastAPI application routes."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from huey.api import app


@pytest.mark.asyncio
async def test_healthz_endpoint_returns_service_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "hueyos"}
