"""Provider connection test boundary and use case service (P02-T04, DEC-003, DEC-007).

Features:
- Lightweight HTTP metadata/auth probes only; strictly NEVER triggers paid token/image generation.
- Never declares a provider CONNECTED without an explicit HTTP 200 response from the probe.
- Distinct states: CONNECTED, INVALID_CREDENTIALS, ACCESS_DENIED, RATE_LIMITED, UNAVAILABLE,
  NOT_CONFIGURED, INVALID_FORMAT, UNKNOWN.
- Measures probe latency in milliseconds (operational metadata only; DEC-018 compliant).
- Sanitizes all exceptions, URLs, headers, and logs to ensure zero secret leakage (ACC-002A).
- Executed on-demand upon explicit user request; never run automatically during server startup.
- Keeps DEC-007 strictly OPEN without introducing unverified external provider SDKs.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.security.key_validator import (
    PROVIDER_VALIDATION_ENDPOINTS,
    validate_key_format,
)
from app.security.masking import mask_secret, redact_text

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """Categorized connection test states for AI providers."""

    CONNECTED = "CONNECTED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCESS_DENIED = "ACCESS_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    INVALID_FORMAT = "INVALID_FORMAT"
    UNKNOWN = "UNKNOWN"


class ProviderConnectionTestResult(BaseModel):
    """Structured, sanitized result of a provider connection test.

    Guarantees raw keys and authorization headers are never exposed or serialized.
    """

    provider: str
    state: ConnectionState
    connected: bool = Field(
        ...,
        description="True strictly and only if probe received HTTP 200 OK from metadata endpoint",
    )
    message: str
    latency_ms: float | None = Field(
        default=None,
        description="Measured round-trip probe latency in milliseconds",
    )
    masked_key: str | None = Field(
        default=None,
        description="Masked key representation (e.g. ••••cdef)",
    )
    http_status: int | None = Field(
        default=None,
        description="HTTP status code returned by metadata probe",
    )
    tested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of the connection test",
    )

    def __repr__(self) -> str:
        return (
            f"ProviderConnectionTestResult(provider={self.provider!r}, "
            f"state={self.state.value!r}, connected={self.connected}, "
            f"latency_ms={self.latency_ms}, masked_key={self.masked_key!r}, "
            f"http_status={self.http_status})"
        )

    def __str__(self) -> str:
        return self.__repr__()


async def test_provider_connection(
    provider: str,
    api_key: str | None,
    timeout_seconds: float = 8.0,
    client: httpx.AsyncClient | None = None,
) -> ProviderConnectionTestResult:
    """Execute an isolated connection test against a provider's metadata/auth endpoint.

    Strict Invariants:
    1. NEVER calls generation endpoints (chat completions, content generation, embeddings).
    2. NEVER sets connected=True unless HTTP 200 OK is received from the provider.
    3. Format validation alone NEVER yields CONNECTED.
    4. Secrets are masked; authorization headers and query parameters are never logged.
    """
    provider_norm = provider.lower()

    # 1. Supported provider check
    if provider_norm not in PROVIDER_VALIDATION_ENDPOINTS:
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.UNKNOWN,
            connected=False,
            message=f"Provider '{provider}' is not supported.",
            masked_key=mask_secret(api_key) if api_key else None,
        )

    # 2. Missing key check
    if api_key is None or not api_key.strip():
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.NOT_CONFIGURED,
            connected=False,
            message=f"No API key configured for {provider_norm.capitalize()} in local .env.",
            masked_key=None,
        )

    masked = mask_secret(api_key)

    # 3. Format/structural validation (fast local check before network)
    is_valid_format, format_reason = validate_key_format(provider_norm, api_key)
    if not is_valid_format:
        logger.info(
            "Connection test format check failed for '%s': %s",
            provider_norm,
            format_reason,
        )
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.INVALID_FORMAT,
            connected=False,
            message=format_reason,
            masked_key=masked,
        )

    # 4. Live metadata probe (low-cost catalog query, zero text/image generation)
    endpoint_info = PROVIDER_VALIDATION_ENDPOINTS[provider_norm]
    url = endpoint_info["url"]
    headers: dict[str, str] = {
        "Accept": "application/json",
        "User-Agent": "ILLUM-AI-STUDIO-ConnectionTest/1.0",
    }

    if endpoint_info.get("auth_type") == "header":
        headers[endpoint_info["auth_header"]] = api_key.strip()
    else:
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout_seconds)
        should_close_client = True

    start_time = time.perf_counter()
    try:
        response = await client.get(url, headers=headers)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status_code = response.status_code

        # HTTP 200: Connected
        if status_code == 200:
            logger.info(
                "Connection test SUCCESS for '%s' (latency: %.2f ms)",
                provider_norm,
                elapsed_ms,
            )
            return ProviderConnectionTestResult(
                provider=provider_norm,
                state=ConnectionState.CONNECTED,
                connected=True,
                message=f"Successfully connected to {provider_norm.capitalize()} metadata API.",
                latency_ms=elapsed_ms,
                masked_key=masked,
                http_status=200,
            )

        # HTTP 401: Invalid Credentials
        if status_code == 401:
            logger.warning(
                "Connection test REJECTED for '%s' (HTTP 401 Unauthorized)",
                provider_norm,
            )
            return ProviderConnectionTestResult(
                provider=provider_norm,
                state=ConnectionState.INVALID_CREDENTIALS,
                connected=False,
                message=f"{provider_norm.capitalize()} rejected credentials (HTTP 401 Unauthorized). Verify API key.",
                latency_ms=elapsed_ms,
                masked_key=masked,
                http_status=401,
            )

        # HTTP 403: Access Denied / Billing
        if status_code == 403:
            logger.warning(
                "Connection test ACCESS DENIED for '%s' (HTTP 403 Forbidden)",
                provider_norm,
            )
            return ProviderConnectionTestResult(
                provider=provider_norm,
                state=ConnectionState.ACCESS_DENIED,
                connected=False,
                message=f"{provider_norm.capitalize()} denied access (HTTP 403 Forbidden). Check project permissions or billing.",
                latency_ms=elapsed_ms,
                masked_key=masked,
                http_status=403,
            )

        # HTTP 429: Rate Limited / Quota
        if status_code == 429:
            logger.warning(
                "Connection test RATE LIMITED for '%s' (HTTP 429 Too Many Requests)",
                provider_norm,
            )
            return ProviderConnectionTestResult(
                provider=provider_norm,
                state=ConnectionState.RATE_LIMITED,
                connected=False,
                message=f"{provider_norm.capitalize()} rate limit or quota exceeded (HTTP 429).",
                latency_ms=elapsed_ms,
                masked_key=masked,
                http_status=429,
            )

        # HTTP 5xx: Service Unavailable
        if status_code in (500, 502, 503, 504):
            logger.warning(
                "Connection test UNAVAILABLE for '%s' (HTTP %d)",
                provider_norm,
                status_code,
            )
            return ProviderConnectionTestResult(
                provider=provider_norm,
                state=ConnectionState.UNAVAILABLE,
                connected=False,
                message=f"{provider_norm.capitalize()} service is temporarily unavailable (HTTP {status_code}).",
                latency_ms=elapsed_ms,
                masked_key=masked,
                http_status=status_code,
            )

        # Other unexpected HTTP response
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.UNAVAILABLE,
            connected=False,
            message=f"{provider_norm.capitalize()} returned unexpected HTTP status {status_code}.",
            latency_ms=elapsed_ms,
            masked_key=masked,
            http_status=status_code,
        )

    except httpx.TimeoutException:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.warning("Connection test TIMEOUT for '%s'", provider_norm)
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.UNAVAILABLE,
            connected=False,
            message=f"Connection to {provider_norm.capitalize()} timed out after {timeout_seconds:.1f}s.",
            latency_ms=elapsed_ms,
            masked_key=masked,
        )

    except (httpx.ConnectError, httpx.NetworkError) as ne:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        sanitized_err = redact_text(str(ne))
        logger.warning(
            "Connection test NETWORK ERROR for '%s': %s",
            provider_norm,
            sanitized_err,
        )
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.UNAVAILABLE,
            connected=False,
            message=f"Could not connect to {provider_norm.capitalize()} endpoint. Check network connectivity.",
            latency_ms=elapsed_ms,
            masked_key=masked,
        )

    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        exc_name = type(exc).__name__
        logger.error(
            "Unexpected connection test exception for '%s': %s",
            provider_norm,
            exc_name,
        )
        return ProviderConnectionTestResult(
            provider=provider_norm,
            state=ConnectionState.UNAVAILABLE,
            connected=False,
            message=f"Connection test failed due to an unexpected error ({exc_name}).",
            latency_ms=elapsed_ms,
            masked_key=masked,
        )

    finally:
        if should_close_client:
            await client.aclose()


async def test_all_provider_connections(
    config: Any = None,
    timeout_seconds: float = 8.0,
    client: httpx.AsyncClient | None = None,
) -> dict[str, ProviderConnectionTestResult]:
    """Execute connection tests for all configured candidate providers.

    Parameters:
        config: AppConfig instance. If None, retrieves global config singleton.
        timeout_seconds: Per-provider network timeout.
        client: Optional shared httpx client for testing.

    Returns:
        dict mapping provider name to ProviderConnectionTestResult.
    """
    from app.config import PROVIDER_KEYS, get_config

    cfg = config if config is not None else get_config()
    results: dict[str, ProviderConnectionTestResult] = {}

    for provider in PROVIDER_KEYS:
        raw_key = cfg.get_raw_key(provider)
        res = await test_provider_connection(
            provider=provider,
            api_key=raw_key,
            timeout_seconds=timeout_seconds,
            client=client,
        )
        results[provider] = res

    return results
