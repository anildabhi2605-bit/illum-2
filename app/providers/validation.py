"""Provider validation boundary (P02-T02, DEC-007).

Separates API key/connection validation from model generation and provider selection.
DEC-007 remains strictly OPEN; no external provider SDKs or automatic failovers.
"""
from __future__ import annotations

from app.security.key_validator import (
    KeyValidationResult,
    ValidationStatus,
    validate_all_keys,
    validate_api_key,
    validate_key_format,
)
from app.use_cases.test_provider_connection import (
    ConnectionState,
    ProviderConnectionTestResult,
    test_all_provider_connections,
    test_provider_connection,
)

__all__ = [
    "ConnectionState",
    "KeyValidationResult",
    "ProviderConnectionTestResult",
    "ValidationStatus",
    "test_all_provider_connections",
    "test_provider_connection",
    "validate_all_keys",
    "validate_api_key",
    "validate_key_format",
]
