"""Unit tests for provider connection test boundary (P02-T04, DEC-003, DEC-007)."""
from __future__ import annotations

import httpx
import pytest

from app.config import AppConfig
from app.security.masking import mask_secret
from app.use_cases.test_provider_connection import (
    ConnectionState,
    ProviderConnectionTestResult,
    test_all_provider_connections as execute_test_all_provider_connections,
    test_provider_connection as execute_test_provider_connection,
)

CANARY_SECRET_GEMINI = "AIzaSyTestCanaryGemini0123456789abcdef"
CANARY_SECRET_GROQ = "gsk_testCanaryGroq0123456789abcdef99"
CANARY_SECRET_OPENAI = "sk-proj-testCanaryOpenAI0123456789abcdef"


class TestConnectionStateCategorization:
    """Verify exact categorization of HTTP response codes to connection states."""

    @pytest.mark.asyncio
    async def test_http_200_yields_connected(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "x-goog-api-key" in request.headers
            assert request.headers["x-goog-api-key"] == CANARY_SECRET_GEMINI
            return httpx.Response(200, json={"models": [{"name": "models/gemini-1.5-flash"}]})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="gemini",
                api_key=CANARY_SECRET_GEMINI,
                client=client,
            )
            assert res.connected is True
            assert res.state == ConnectionState.CONNECTED
            assert res.http_status == 200
            assert res.latency_ms is not None
            assert res.latency_ms >= 0.0
            assert res.masked_key == mask_secret(CANARY_SECRET_GEMINI)
            assert "successfully" in res.message.lower()

    @pytest.mark.asyncio
    async def test_http_401_yields_invalid_credentials(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": {"message": "Invalid API Key"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="groq",
                api_key=CANARY_SECRET_GROQ,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.INVALID_CREDENTIALS
            assert res.http_status == 401
            assert "401" in res.message
            assert CANARY_SECRET_GROQ not in res.message

    @pytest.mark.asyncio
    async def test_http_403_yields_access_denied(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"error": {"message": "Access Forbidden"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="openai",
                api_key=CANARY_SECRET_OPENAI,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.ACCESS_DENIED
            assert res.http_status == 403
            assert "403" in res.message

    @pytest.mark.asyncio
    async def test_http_429_yields_rate_limited(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "Quota exceeded"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="groq",
                api_key=CANARY_SECRET_GROQ,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.RATE_LIMITED
            assert res.http_status == 429
            assert "429" in res.message

    @pytest.mark.asyncio
    async def test_http_503_yields_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="gemini",
                api_key=CANARY_SECRET_GEMINI,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.UNAVAILABLE
            assert res.http_status == 503
            assert "unavailable" in res.message.lower()

    @pytest.mark.asyncio
    async def test_network_timeout_yields_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Read timed out")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="groq",
                api_key=CANARY_SECRET_GROQ,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.UNAVAILABLE
            assert "timed out" in res.message.lower()

    @pytest.mark.asyncio
    async def test_network_connect_error_yields_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="openai",
                api_key=CANARY_SECRET_OPENAI,
                client=client,
            )
            assert res.connected is False
            assert res.state == ConnectionState.UNAVAILABLE
            assert "could not connect" in res.message.lower()


class TestStrictNonConnectedInvariants:
    """Verify that unprobed or invalid states NEVER claim connected=True."""

    @pytest.mark.asyncio
    async def test_unconfigured_key_never_connected(self):
        res = await execute_test_provider_connection(provider="gemini", api_key=None)
        assert res.connected is False
        assert res.state == ConnectionState.NOT_CONFIGURED
        assert res.masked_key is None
        assert "no api key" in res.message.lower()

    @pytest.mark.asyncio
    async def test_invalid_format_never_connected(self):
        # Placeholder or malformed keys must fail locally before making any network probe
        res = await execute_test_provider_connection(
            provider="gemini",
            api_key="your_gemini_api_key_here",
        )
        assert res.connected is False
        assert res.state == ConnectionState.INVALID_FORMAT
        assert "placeholder" in res.message.lower()

    @pytest.mark.asyncio
    async def test_unknown_provider_never_connected(self):
        res = await execute_test_provider_connection(
            provider="unsupported_model_provider",
            api_key="some_key_1234567890123456789",
        )
        assert res.connected is False
        assert res.state == ConnectionState.UNKNOWN
        assert "not supported" in res.message.lower()


class TestSecretSanitizationAndCanaryProtection:
    """Verify that raw keys and authorization headers are never disclosed."""

    def test_result_string_representation_masks_secrets(self):
        res = ProviderConnectionTestResult(
            provider="groq",
            state=ConnectionState.CONNECTED,
            connected=True,
            message="Connected",
            masked_key=mask_secret(CANARY_SECRET_GROQ),
            latency_ms=12.5,
        )
        # Canary raw string must not appear in repr, str, or model_dump
        assert CANARY_SECRET_GROQ not in repr(res)
        assert CANARY_SECRET_GROQ not in str(res)
        assert CANARY_SECRET_GROQ not in str(res.model_dump())
        assert "••••" in repr(res)

    @pytest.mark.asyncio
    async def test_provider_error_payload_never_leaks_key(self):
        def handler(request: httpx.Request) -> httpx.Response:
            # Simulated malicious/verbose provider echo
            return httpx.Response(
                401,
                json={"error": f"Invalid key provided: {CANARY_SECRET_GROQ}"},
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await execute_test_provider_connection(
                provider="groq",
                api_key=CANARY_SECRET_GROQ,
                client=client,
            )
            assert CANARY_SECRET_GROQ not in res.message
            assert CANARY_SECRET_GROQ not in repr(res)


class TestTestAllProviderConnections:
    """Verify multi-provider connection test orchestration."""

    @pytest.mark.asyncio
    async def test_test_all_connections_with_mock_client(self):
        config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": CANARY_SECRET_GEMINI,
                "GROQ_API_KEY": CANARY_SECRET_GROQ,
            }
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            results = await execute_test_all_provider_connections(
                config=config,
                client=client,
            )

            # Gemini and Groq were configured -> CONNECTED
            assert results["gemini"].connected is True
            assert results["gemini"].state == ConnectionState.CONNECTED
            assert results["groq"].connected is True
            assert results["groq"].state == ConnectionState.CONNECTED

            # OpenAI and OpenRouter were not configured -> NOT_CONFIGURED
            assert results["openai"].connected is False
            assert results["openai"].state == ConnectionState.NOT_CONFIGURED
            assert results["openrouter"].connected is False
            assert results["openrouter"].state == ConnectionState.NOT_CONFIGURED
