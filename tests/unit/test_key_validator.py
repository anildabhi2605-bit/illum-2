"""Unit tests for safe API key validation (P02-T02, ACC-002A, DEC-003, DEC-007)."""
from __future__ import annotations

import httpx
import pytest

from app.config import AppConfig
from app.security.key_validator import (
    KeyValidationResult,
    ValidationStatus,
    validate_all_keys,
    validate_api_key,
    validate_key_format,
)
from app.security.masking import mask_secret

SENTINEL_GROQ = "gsk_testvalid0123456789abcdef998877"
SENTINEL_OPENAI = "sk-proj-testvalid0123456789abcdef9988"
SENTINEL_OPENROUTER = "sk-or-v1-testvalid0123456789abcdef9988"
SENTINEL_GEMINI = "AIzaSyTestValid0123456789abcdef9988776655"


class TestKeyFormatValidation:
    """Verify local format and placeholder validation logic."""

    def test_missing_or_empty_key_rejected(self):
        valid, msg = validate_key_format("gemini", None)
        assert valid is False
        assert "No API key" in msg

        valid, msg = validate_key_format("groq", "   ")
        assert valid is False
        assert "No API key" in msg

    def test_placeholder_templates_rejected(self):
        placeholders = [
            ("gemini", "your_gemini_api_key_here"),
            ("groq", "your_groq_api_key_here"),
            ("openai", "your_openai_api_key_here"),
            ("openrouter", "your_openrouter_api_key_here"),
            ("gemini", "PLACEHOLDER_KEY"),
            ("groq", "changeme"),
        ]
        for provider, ph in placeholders:
            valid, msg = validate_key_format(provider, ph)
            assert valid is False
            assert "placeholder" in msg.lower()

    def test_whitespace_and_newlines_rejected(self):
        bad_keys = [
            "gsk_validprefix with space12345",
            "sk-validprefix\nwithnewline12345",
            "AIzaSyTest\twithtab1234567890",
        ]
        for key in bad_keys:
            valid, msg = validate_key_format("groq", key)
            assert valid is False
            assert "whitespace" in msg.lower() or "illegal" in msg.lower()

    def test_unusually_short_key_rejected(self):
        valid, msg = validate_key_format("gemini", "short123")
        assert valid is False
        assert "short" in msg.lower()

    def test_groq_format_checks(self):
        # Must start with gsk_
        valid, msg = validate_key_format("groq", "badprefix0123456789abcdef012345")
        assert valid is False
        assert "gsk_" in msg

        # Valid groq key format
        valid, msg = validate_key_format("groq", SENTINEL_GROQ)
        assert valid is True

    def test_openai_format_checks(self):
        # Must start with sk-
        valid, msg = validate_key_format("openai", "invalidprefix01234567890123456789")
        assert valid is False
        assert "sk-" in msg

        # Valid openai key format
        valid, msg = validate_key_format("openai", SENTINEL_OPENAI)
        assert valid is True

    def test_openrouter_format_checks(self):
        # Must start with sk-
        valid, msg = validate_key_format("openrouter", "badprefix01234567890123456789")
        assert valid is False
        assert "sk-" in msg

        # Valid openrouter key format
        valid, msg = validate_key_format("openrouter", SENTINEL_OPENROUTER)
        assert valid is True

    def test_gemini_format_checks(self):
        # Invalid characters
        valid, msg = validate_key_format("gemini", "AIzaSyTest!@#$%^&*()_+1234567890")
        assert valid is False

        # Valid gemini key format
        valid, msg = validate_key_format("gemini", SENTINEL_GEMINI)
        assert valid is True


class TestLiveKeyValidationProbes:
    """Verify live endpoint probe handling with mock responses."""

    @pytest.mark.asyncio
    async def test_unknown_provider_handling(self):
        res = await validate_api_key(
            provider="unsupported_ai",
            api_key="some_key_123456789012345",
        )
        assert res.valid is False
        assert res.status == ValidationStatus.UNKNOWN_PROVIDER
        assert "unsupported_ai" in res.message

    @pytest.mark.asyncio
    async def test_not_configured_handling(self):
        res = await validate_api_key(provider="gemini", api_key=None)
        assert res.valid is False
        assert res.status == ValidationStatus.NOT_CONFIGURED
        assert res.masked_key is None
        assert "No API key" in res.message

    @pytest.mark.asyncio
    async def test_offline_mode_skips_network(self):
        res = await validate_api_key(
            provider="groq",
            api_key=SENTINEL_GROQ,
            online=False,
        )
        assert res.valid is True
        assert res.status == ValidationStatus.VALID
        assert "offline" in res.message.lower()
        assert res.masked_key == mask_secret(SENTINEL_GROQ)

    @pytest.mark.asyncio
    async def test_mock_http_200_valid(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "x-goog-api-key" in request.headers
            assert request.headers["x-goog-api-key"] == SENTINEL_GEMINI
            return httpx.Response(200, json={"models": [{"name": "models/gemini-1.5-flash"}]})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="gemini",
                api_key=SENTINEL_GEMINI,
                client=client,
            )
            assert res.valid is True
            assert res.status == ValidationStatus.VALID
            assert res.http_status == 200
            assert "connected" in res.message.lower()
            assert res.masked_key == mask_secret(SENTINEL_GEMINI)

    @pytest.mark.asyncio
    async def test_mock_http_401_invalid_key(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": {"message": "Invalid API Key"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="groq",
                api_key=SENTINEL_GROQ,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.INVALID_KEY
            assert res.http_status == 401
            assert "401" in res.message
            assert SENTINEL_GROQ not in res.message
            assert res.masked_key == mask_secret(SENTINEL_GROQ)

    @pytest.mark.asyncio
    async def test_mock_http_403_forbidden(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"error": {"message": "Access denied"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="openai",
                api_key=SENTINEL_OPENAI,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.INVALID_KEY
            assert res.http_status == 403
            assert "403" in res.message

    @pytest.mark.asyncio
    async def test_mock_http_429_rate_limited(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": {"message": "Rate limit reached"}})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="openrouter",
                api_key=SENTINEL_OPENROUTER,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.RATE_LIMITED
            assert res.http_status == 429
            assert "429" in res.message

    @pytest.mark.asyncio
    async def test_mock_http_503_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="Service Unavailable")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="gemini",
                api_key=SENTINEL_GEMINI,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.UNAVAILABLE
            assert res.http_status == 503
            assert "unavailable" in res.message.lower()

    @pytest.mark.asyncio
    async def test_mock_network_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Timeout connecting to server")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="groq",
                api_key=SENTINEL_GROQ,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.UNAVAILABLE
            assert "timed out" in res.message.lower()

    @pytest.mark.asyncio
    async def test_mock_network_connect_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="openai",
                api_key=SENTINEL_OPENAI,
                client=client,
            )
            assert res.valid is False
            assert res.status == ValidationStatus.UNAVAILABLE
            assert "could not reach" in res.message.lower()


class TestValidateAllKeys:
    """Verify multi-provider validation runner."""

    @pytest.mark.asyncio
    async def test_validate_all_with_config(self):
        config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": SENTINEL_GEMINI,
                "GROQ_API_KEY": SENTINEL_GROQ,
            }
        )

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": []})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            results = await validate_all_keys(config=config, client=client, online=True)

            assert "gemini" in results
            assert "groq" in results
            assert "openai" in results
            assert "openrouter" in results

            # Gemini and Groq were configured
            assert results["gemini"].valid is True
            assert results["gemini"].status == ValidationStatus.VALID
            assert results["groq"].valid is True
            assert results["groq"].status == ValidationStatus.VALID

            # OpenAI and OpenRouter were not configured
            assert results["openai"].valid is False
            assert results["openai"].status == ValidationStatus.NOT_CONFIGURED
            assert results["openrouter"].valid is False
            assert results["openrouter"].status == ValidationStatus.NOT_CONFIGURED


class TestKeyValidatorSecurityBoundaries:
    """Verify strict secret isolation and redaction during validation."""

    def test_result_string_representation_masks_secrets(self):
        result = KeyValidationResult(
            provider="gemini",
            status=ValidationStatus.VALID,
            valid=True,
            message="Valid key",
            masked_key=mask_secret(SENTINEL_GEMINI),
        )
        # Raw sentinel must NOT be in repr or str
        assert SENTINEL_GEMINI not in repr(result)
        assert SENTINEL_GEMINI not in str(result)
        assert SENTINEL_GEMINI not in str(result.model_dump())
        assert "••••" in repr(result)

    @pytest.mark.asyncio
    async def test_error_message_never_reflects_raw_key(self):
        raw_secret_key = "gsk_supersecret1234567890abcdef9988"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": f"Invalid key {raw_secret_key}"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            res = await validate_api_key(
                provider="groq",
                api_key=raw_secret_key,
                client=client,
            )
            assert raw_secret_key not in res.message
            assert res.masked_key == mask_secret(raw_secret_key)
            assert raw_secret_key not in repr(res)
