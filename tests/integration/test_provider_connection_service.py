"""Integration tests for provider connection test endpoints (P02-T04, DEC-003, DEC-007)."""
from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.config import AppConfig, reset_config
from app.main import app

CANARY_GROQ = "gsk_integCanary0123456789abcdef9988"


@pytest.fixture(autouse=True)
def clean_config_environment():
    reset_config()
    yield
    reset_config()


class TestProviderConnectionEndpoints:
    """Verify HTTP endpoints /api/providers/test-connection and /api/providers/{provider}/test-connection."""

    @pytest.mark.asyncio
    async def test_test_all_connections_unconfigured_default(self):
        # Configure app with zero keys
        app.state.config = AppConfig(raw_values={})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/providers/test-connection")
            assert resp.status_code == 200
            data = resp.json()
            assert "connections" in data
            connections = data["connections"]

            for provider in ["gemini", "groq", "openai", "openrouter"]:
                assert provider in connections
                item = connections[provider]
                assert item["connected"] is False
                assert item["state"] == "NOT_CONFIGURED"
                assert item["masked_key"] is None

    @pytest.mark.asyncio
    async def test_test_single_provider_not_configured(self):
        app.state.config = AppConfig(raw_values={})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/providers/groq/test-connection")
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "groq"
            assert data["connected"] is False
            assert data["state"] == "NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_test_single_provider_unknown(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/providers/unknown_ai_provider/test-connection")
            assert resp.status_code == 200
            data = resp.json()
            assert data["connected"] is False
            assert data["state"] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_test_single_provider_invalid_format(self):
        # Configure placeholder key in app
        app.state.config = AppConfig(raw_values={"GROQ_API_KEY": "your_groq_api_key_here"})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/providers/groq/test-connection")
            assert resp.status_code == 200
            data = resp.json()
            assert data["connected"] is False
            assert data["state"] == "INVALID_FORMAT"
            assert "placeholder" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_canary_secret_never_leaked_in_endpoint_response(self):
        app.state.config = AppConfig(raw_values={"GROQ_API_KEY": CANARY_GROQ})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/providers/groq/test-connection")
            assert resp.status_code == 200
            data = resp.json()
            # Raw key must NEVER appear in the response payload or headers
            assert CANARY_GROQ not in resp.text
            assert data["masked_key"] is not None
            assert "••••" in data["masked_key"]
