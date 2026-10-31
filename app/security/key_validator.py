"""Safe API key validation service (P02-T02, ACC-002A, ACC-003, DEC-003, DEC-007).

Features:
- Validates configured API keys for supported providers (Gemini, Groq, OpenAI, OpenRouter).
- Never exposes, prints, or logs raw API key values in exceptions, logs, or responses.
- Provides two-phase validation: fast offline format/placeholder check, followed by
  low-cost online metadata/auth endpoint probe.
- Distinct status states: VALID, INVALID_KEY, INVALID_FORMAT, RATE_LIMITED, UNAVAILABLE,
  NOT_CONFIGURED, UNKNOWN_PROVIDER.
- Keeps key validation strictly separate from provider selection and model routing.
- Never silently switches providers or models.
"""
from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.security.masking import mask_secret, redact_text

logger = logging.getLogger(__name__)

# Known placeholder patterns in .env.example or unconfigured environments
KNOWN_PLACEHOLDERS: set[str] = {
    "your_gemini_api_key_here",
    "your_groq_api_key_here",
    "your_openai_api_key_here",
    "your_openrouter_api_key_here",
    "your_api_key_here",
    "your-api-key-here",
    "placeholder",
    "changeme",
    "todo",
    "example",
}

# Provider endpoint metadata for low-cost validation (metadata probe only, no generation)
PROVIDER_VALIDATION_ENDPOINTS: dict[str, dict[str, Any]] = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        "method": "GET",
        "auth_type": "header",
        "auth_header": "x-goog-api-key",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "method": "GET",
        "auth_type": "bearer",
    },
    "openai": {
        "url": "https://api.openai.com/v1/models",
        "method": "GET",
        "auth_type": "bearer",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/auth/key",
        "method": "GET",
        "auth_type": "bearer",
    },
}


class ValidationStatus(str, Enum):
    """Categorized status states for API key validation."""

    VALID = "VALID"
    INVALID_KEY = "INVALID_KEY"
    INVALID_FORMAT = "INVALID_FORMAT"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"


class KeyValidationResult(BaseModel):
    """Sanitized validation outcome for an API key.

    Guarantees raw secret values are never included or serialized.
    """

    provider: str
    status: ValidationStatus
    valid: bool
    message: str
    masked_key: str | None = None
    http_status: int | None = Field(default=None, description="HTTP status code from provider endpoint")

    def __repr__(self) -> str:
        return (
            f"KeyValidationResult(provider={self.provider!r}, status={self.status.value!r}, "
            f"valid={self.valid}, masked_key={self.masked_key!r}, http_status={self.http_status})"
        )

    def __str__(self) -> str:
        return self.__repr__()


def validate_key_format(provider: str, api_key: str | None) -> tuple[bool, str]:
    """Perform local structural and format validation on an API key without network calls.

    Returns:
        (is_valid, reason_message)
    """
    if api_key is None or not api_key.strip():
        return False, "No API key configured."

    key_clean = api_key.strip()
    key_lower = key_clean.lower()

    # Check for placeholder template values
    if key_lower in KNOWN_PLACEHOLDERS or any(
        p in key_lower for p in ["your_", "_key_here", "placeholder", "changeme", "example"]
    ):
        return (
            False,
            "API key appears to be a placeholder template value. Please replace with your actual API key.",
        )

    # Check for whitespace, newlines or control characters
    if any(c.isspace() for c in key_clean):
        return False, "API key contains illegal whitespace or newline characters."

    # Non-printable characters check
    if not key_clean.isascii() or not key_clean.isprintable():
        return False, "API key contains non-ASCII or non-printable characters."

    # Minimum length sanity check
    if len(key_clean) < 12:
        return False, "API key length is unusually short (fewer than 12 characters)."

    provider_norm = provider.lower()

    if provider_norm == "groq":
        # Groq keys generally start with 'gsk_'
        if not key_clean.startswith("gsk_"):
            return False, "Groq API key format invalid: expected prefix 'gsk_'."
        if len(key_clean) < 25:
            return False, "Groq API key format invalid: key is shorter than expected."

    elif provider_norm == "openai":
        # OpenAI keys generally start with 'sk-' or 'sk-proj-'
        if not key_clean.startswith("sk-"):
            return False, "OpenAI API key format invalid: expected prefix 'sk-'."
        if len(key_clean) < 20:
            return False, "OpenAI API key format invalid: key is shorter than expected."

    elif provider_norm == "openrouter":
        # OpenRouter keys generally start with 'sk-or-' or 'sk-'
        if not key_clean.startswith("sk-"):
            return False, "OpenRouter API key format invalid: expected prefix 'sk-'."
        if len(key_clean) < 20:
            return False, "OpenRouter API key format invalid: key is shorter than expected."

    elif provider_norm == "gemini":
        # Google Gemini / AI Studio keys are alphanumeric/dashes/underscores
        if not re.match(r"^[A-Za-z0-9_-]{20,64}$", key_clean):
            return False, "Gemini API key format invalid: contains unexpected characters or invalid length."

    return True, "Key format is valid."


async def validate_api_key(
    provider: str,
    api_key: str | None,
    timeout_seconds: float = 8.0,
    client: httpx.AsyncClient | None = None,
    online: bool = True,
) -> KeyValidationResult:
    """Validate a single provider API key safely.

    Parameters:
        provider: Provider name ('gemini', 'groq', 'openai', 'openrouter')
        api_key: Raw API key (or None)
        timeout_seconds: Max network wait time (default 8s)
        client: Optional pre-configured httpx.AsyncClient (for testing/mocking)
        online: If True, performs live HTTP metadata probe; if False, format-check only.

    Returns:
        KeyValidationResult with sanitized message and masked key.
    """
    provider_norm = provider.lower()

    if provider_norm not in PROVIDER_VALIDATION_ENDPOINTS:
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.UNKNOWN_PROVIDER,
            valid=False,
            message=f"Provider '{provider}' is not a recognized provider.",
            masked_key=mask_secret(api_key) if api_key else None,
        )

    # 1. Missing key check
    if api_key is None or not api_key.strip():
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.NOT_CONFIGURED,
            valid=False,
            message=f"No API key configured for {provider_norm.capitalize()}.",
            masked_key=None,
        )

    masked = mask_secret(api_key)

    # 2. Local format check
    is_valid_format, format_reason = validate_key_format(provider_norm, api_key)
    if not is_valid_format:
        logger.info("Format validation failed for provider '%s': %s", provider_norm, format_reason)
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.INVALID_FORMAT,
            valid=False,
            message=format_reason,
            masked_key=masked,
        )

    # 3. Offline-only check requested
    if not online:
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.VALID,
            valid=True,
            message=f"{provider_norm.capitalize()} API key format validated (offline check).",
            masked_key=masked,
        )

    # 4. Live network metadata probe
    endpoint_info = PROVIDER_VALIDATION_ENDPOINTS[provider_norm]
    url = endpoint_info["url"]
    headers: dict[str, str] = {
        "Accept": "application/json",
        "User-Agent": "ILLUM-AI-STUDIO-Validator/1.0",
    }

    if endpoint_info.get("auth_type") == "header":
        headers[endpoint_info["auth_header"]] = api_key.strip()
    else:
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout_seconds)
        should_close_client = True

    try:
        response = await client.get(url, headers=headers)
        status_code = response.status_code

        if status_code == 200:
            logger.info("API key validation SUCCESS for provider '%s'", provider_norm)
            return KeyValidationResult(
                provider=provider_norm,
                status=ValidationStatus.VALID,
                valid=True,
                message=f"{provider_norm.capitalize()} API key is valid and connected.",
                masked_key=masked,
                http_status=200,
            )

        if status_code == 401:
            logger.warning("API key validation REJECTED for provider '%s' (HTTP 401)", provider_norm)
            return KeyValidationResult(
                provider=provider_norm,
                status=ValidationStatus.INVALID_KEY,
                valid=False,
                message=f"{provider_norm.capitalize()} rejected the API key (HTTP 401 Unauthorized). Check that your key is active and correctly copied.",
                masked_key=masked,
                http_status=401,
            )

        if status_code == 403:
            logger.warning("API key validation FORBIDDEN for provider '%s' (HTTP 403)", provider_norm)
            return KeyValidationResult(
                provider=provider_norm,
                status=ValidationStatus.INVALID_KEY,
                valid=False,
                message=f"{provider_norm.capitalize()} denied access with this API key (HTTP 403 Forbidden). Check your account permissions, project setup, or billing status.",
                masked_key=masked,
                http_status=403,
            )

        if status_code == 429:
            logger.warning("API key validation RATE LIMITED for provider '%s' (HTTP 429)", provider_norm)
            return KeyValidationResult(
                provider=provider_norm,
                status=ValidationStatus.RATE_LIMITED,
                valid=False,
                message=f"{provider_norm.capitalize()} returned rate limit or quota exceeded (HTTP 429 Too Many Requests).",
                masked_key=masked,
                http_status=429,
            )

        if status_code in (500, 502, 503, 504):
            logger.warning("API key validation UNAVAILABLE for provider '%s' (HTTP %d)", provider_norm, status_code)
            return KeyValidationResult(
                provider=provider_norm,
                status=ValidationStatus.UNAVAILABLE,
                valid=False,
                message=f"{provider_norm.capitalize()} service is temporarily unavailable (HTTP {status_code}). Please try again later.",
                masked_key=masked,
                http_status=status_code,
            )

        # Other HTTP response codes
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.UNAVAILABLE,
            valid=False,
            message=f"{provider_norm.capitalize()} returned unexpected HTTP {status_code} during validation probe.",
            masked_key=masked,
            http_status=status_code,
        )

    except httpx.TimeoutException:
        logger.warning("API key validation TIMEOUT for provider '%s'", provider_norm)
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.UNAVAILABLE,
            valid=False,
            message=f"Connection to {provider_norm.capitalize()} timed out after {timeout_seconds:.1f}s. Check network connectivity.",
            masked_key=masked,
        )

    except (httpx.ConnectError, httpx.NetworkError) as ne:
        err_sanitized = redact_text(str(ne))
        logger.warning("API key validation NETWORK ERROR for provider '%s': %s", provider_norm, err_sanitized)
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.UNAVAILABLE,
            valid=False,
            message=f"Could not reach {provider_norm.capitalize()} endpoint. Check network connectivity or firewall.",
            masked_key=masked,
        )

    except Exception as exc:
        exc_type = type(exc).__name__
        logger.error("Unexpected exception validating key for '%s': %s", provider_norm, exc_type)
        return KeyValidationResult(
            provider=provider_norm,
            status=ValidationStatus.UNAVAILABLE,
            valid=False,
            message=f"Validation failed due to unexpected error ({exc_type}).",
            masked_key=masked,
        )

    finally:
        if should_close_client:
            await client.aclose()


async def validate_all_keys(
    config: Any = None,
    online: bool = True,
    timeout_seconds: float = 8.0,
    client: httpx.AsyncClient | None = None,
) -> dict[str, KeyValidationResult]:
    """Validate all configured provider keys from application configuration.

    Parameters:
        config: AppConfig instance. If None, retrieves global config.
        online: Whether to run live network validation probes.
        timeout_seconds: Probe timeout per request.
        client: Optional shared httpx client.

    Returns:
        dict mapping provider name to KeyValidationResult.
    """
    from app.config import PROVIDER_KEYS, get_config

    cfg = config if config is not None else get_config()
    results: dict[str, KeyValidationResult] = {}

    for provider in PROVIDER_KEYS:
        raw_key = cfg.get_raw_key(provider)
        res = await validate_api_key(
            provider=provider,
            api_key=raw_key,
            timeout_seconds=timeout_seconds,
            client=client,
            online=online,
        )
        results[provider] = res

    return results
