"""Integration tests for key validation endpoints (P02-T02, ACC-002A, ACC-003)."""
from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.config import AppConfig
from app.main import app

SENTINEL_KEY = "gsk_integvalid0123456789abcdef00"


class TestKeyValidationEndpoints:
    """Verify HTTP endpoints /api/config/validate and /api/config/validate/{provider}."""

    @pytest.mark.asyncio
    async def test_validate_all_keys_offline(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/config/validate?online=false")
            assert resp.status_code == 200
            data = resp.json()
            assert "providers" in data
            providers = data["providers"]
            assert "gemini" in providers
            assert "groq" in providers
            assert "openai" in providers
            assert "openrouter" in providers

            # Check structure of each provider result
            for name, res in providers.items():
                assert "provider" in res
                assert "status" in res
                assert "valid" in res
                assert "message" in res
                assert "masked_key" in res

    @pytest.mark.asyncio
    async def test_validate_single_provider_unconfigured(self):
        # Configure app with no keys
        app.state.config = AppConfig(raw_values={})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/config/validate/groq?online=false")
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "groq"
            assert data["valid"] is False
            assert data["status"] == "NOT_CONFIGURED"
            assert data["masked_key"] is None

    @pytest.mark.asyncio
    async def test_validate_single_provider_unknown(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/config/validate/nonexistent_ai?online=false")
            assert resp.status_code == 200
            data = resp.json()
            assert data["valid"] is False
            assert data["status"] == "UNKNOWN_PROVIDER"

    @pytest.mark.asyncio
    async def test_validate_single_provider_configured_format(self):
        # Inject valid format key
        app.state.config = AppConfig(raw_values={"GROQ_API_KEY": SENTINEL_KEY})

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.post("/api/config/validate/groq?online=false")
            assert resp.status_code == 200
            data = resp.json()
            assert data["provider"] == "groq"
            assert data["valid"] is True
            assert data["status"] == "VALID"
            # Masked key is present, raw key is NOT present
            assert data["masked_key"] is not None
            assert "••••" in data["masked_key"]
            assert SENTINEL_KEY not in resp.text
