"""Typed configuration loader and secret safety container (P02-T01, ACC-002A, ACC-003).

Features:
- Strict local .env file loading with missing-file and empty-file fallbacks.
- Typed Pydantic schemas validating non-secret settings and allowed enums.
- Sanitized validation errors that never expose raw API keys or tokens.
- Strict separation of public non-secret configuration from secret values.
- Raw keys accessible only to internal backend adapters; never serialized to UI.
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator

from app.security.env_loader import (
    clear_app_managed_env,
    get_app_managed_keys,
    load_local_env,
    resolve_local_env_path,
)
from app.security.masking import mask_secret

logger = logging.getLogger(__name__)

# Known supported/candidate provider keys
PROVIDER_KEYS: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


class AppEnv(str, Enum):
    """Allowed application lifecycle environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Allowed application logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AllowedProvider(str, Enum):
    """Candidate AI model provider identifiers."""

    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    OPENROUTER = "openrouter"


class ConfigValidationError(ValueError):
    """Sanitized validation error for configuration values.

    Guarantees that sensitive secrets or tokens are never echoed in error messages.
    """

    pass


class PublicSettings(BaseModel):
    """Non-secret application settings safe for serialization and inspection."""

    app_env: AppEnv = AppEnv.DEVELOPMENT
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1024, le=65535)
    default_provider: AllowedProvider = AllowedProvider.GEMINI
    default_model: str = "gemini-1.5-flash"
    log_level: LogLevel = LogLevel.INFO

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Host cannot be empty.")
        return v_clean

    @field_validator("default_model")
    @classmethod
    def validate_default_model(cls, v: str) -> str:
        v_clean = v.strip()
        if not v_clean:
            raise ValueError("Default model name cannot be empty.")
        return v_clean


class ProviderSecrets(BaseModel):
    """Secret API credentials container.

    Enforces SecretStr masking and strict exclusion from serialized output.
    """

    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    @field_validator(
        "gemini_api_key",
        "groq_api_key",
        "openai_api_key",
        "openrouter_api_key",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return v

    def __repr__(self) -> str:
        return "ProviderSecrets(<protected>)"

    def __str__(self) -> str:
        return "ProviderSecrets(<protected>)"


class AppConfig:
    """Application configuration container managing typed public settings and secrets."""

    def __init__(
        self,
        env_file: Path | str | None = None,
        project_root: Path | None = None,
        raw_values: dict[str, str] | None = None,
        enforce_boundary: bool = True,
    ) -> None:
        """Initialize configuration with strict local .env loader and missing-file fallback."""
        target_env_path = resolve_local_env_path(
            env_file=env_file,
            project_root=project_root,
            enforce_boundary=enforce_boundary,
        )
        env_file_exists = target_env_path.exists()

        loaded_env: dict[str, str] = {}
        if raw_values is not None:
            loaded_env.update(raw_values)
        else:
            loaded_env = load_local_env(
                env_file=env_file,
                project_root=project_root,
                apply_to_environ=True,
                override=False,
                enforce_boundary=enforce_boundary,
            )

        # Define explicit configuration precedence:
        # Precedence 1: Explicit raw_values (programmatic test injection)
        # Precedence 2: Local .env file values (Notepad-edited local configuration)
        # Precedence 3: External environment variables (system settings not in .env)
        # Precedence 4: Built-in default values
        def _get_val(key: str, default: str | None = None) -> str | None:
            # 1. Programmatic raw_values override (highest precedence)
            if raw_values is not None:
                if key in raw_values:
                    return raw_values[key]
                return default

            # 2. Provider secret keys (GEMINI_API_KEY, GROQ_API_KEY, etc.)
            if key in PROVIDER_KEYS.values():
                if env_file_exists:
                    # When .env file exists, only non-empty entries in .env configure the provider
                    v = loaded_env.get(key)
                    return v.strip() if (v and v.strip()) else None
                # If no .env file exists on disk, check os.environ directly (supports test fixtures & missing-file fallback)
                v = os.getenv(key)
                return v.strip() if (v and v.strip()) else None

            # 3. Non-secret public settings (PORT, HOST, APP_ENV, etc.)
            # External os.environ takes precedence over .env for system launch flags
            app_managed = get_app_managed_keys()
            if key in os.environ and key not in app_managed:
                v = os.environ[key].strip()
                if v:
                    return v

            if key in loaded_env:
                v = loaded_env[key].strip()
                if v:
                    return v

            val = os.getenv(key)
            if val is not None and val.strip():
                return val.strip()

            return default

        # Validate non-secret public settings
        raw_port = _get_val("PORT", "8000")
        try:
            port_val = int(raw_port) if raw_port is not None else 8000
        except ValueError:
            raise ConfigValidationError(
                f"Invalid configuration for PORT: '{raw_port}' is not a valid integer."
            )

        raw_env = (_get_val("APP_ENV", "development") or "development").lower()
        try:
            app_env_val = AppEnv(raw_env)
        except ValueError:
            allowed = [e.value for e in AppEnv]
            raise ConfigValidationError(
                f"Invalid configuration for APP_ENV: '{raw_env}'. Allowed values: {allowed}."
            )

        raw_provider = (_get_val("DEFAULT_PROVIDER", "gemini") or "gemini").lower()
        try:
            provider_val = AllowedProvider(raw_provider)
        except ValueError:
            allowed_p = [p.value for p in AllowedProvider]
            raise ConfigValidationError(
                f"Invalid configuration for DEFAULT_PROVIDER: '{raw_provider}'. Allowed values: {allowed_p}."
            )

        raw_log = (_get_val("LOG_LEVEL", "INFO") or "INFO").upper()
        try:
            log_level_val = LogLevel(raw_log)
        except ValueError:
            allowed_levels = [level.value for level in LogLevel]
            raise ConfigValidationError(
                f"Invalid configuration for LOG_LEVEL: '{raw_log}'. Allowed values: {allowed_levels}."
            )

        try:
            self._public = PublicSettings(
                app_env=app_env_val,
                host=_get_val("HOST", "127.0.0.1") or "127.0.0.1",
                port=port_val,
                default_provider=provider_val,
                default_model=_get_val("DEFAULT_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash",
                log_level=log_level_val,
            )
        except ValidationError as ve:
            # Sanitize error to avoid reflecting unvalidated input
            errors = [f"{e['loc'][0]}: {e['msg']}" for e in ve.errors()]
            raise ConfigValidationError(f"Configuration validation failed: {'; '.join(errors)}")

        # Load secrets with SecretStr protection
        self._secrets = ProviderSecrets(
            gemini_api_key=_get_val("GEMINI_API_KEY"),
            groq_api_key=_get_val("GROQ_API_KEY"),
            openai_api_key=_get_val("OPENAI_API_KEY"),
            openrouter_api_key=_get_val("OPENROUTER_API_KEY"),
        )

    # Public settings properties
    @property
    def public(self) -> PublicSettings:
        return self._public

    @property
    def secrets(self) -> ProviderSecrets:
        return self._secrets

    @property
    def app_env(self) -> str:
        return self._public.app_env.value

    @property
    def host(self) -> str:
        return self._public.host

    @property
    def port(self) -> int:
        return self._public.port

    @property
    def default_provider(self) -> str:
        return self._public.default_provider.value

    @property
    def default_model(self) -> str:
        return self._public.default_model

    @property
    def log_level(self) -> str:
        return self._public.log_level.value

    def get_raw_key(self, provider: str) -> str | None:
        """Retrieve raw API key for backend adapters only. Never pass to frontend or logs."""
        provider_norm = provider.lower()
        if provider_norm == "gemini":
            secret = self._secrets.gemini_api_key
        elif provider_norm == "groq":
            secret = self._secrets.groq_api_key
        elif provider_norm == "openai":
            secret = self._secrets.openai_api_key
        elif provider_norm == "openrouter":
            secret = self._secrets.openrouter_api_key
        else:
            return None

        if secret is None:
            return None
        raw = secret.get_secret_value()
        return raw if raw else None

    def is_provider_configured(self, provider: str) -> bool:
        """Check if an API key is present and non-empty for the given provider."""
        return self.get_raw_key(provider) is not None

    def get_provider_status(self, provider: str) -> dict[str, Any]:
        """Return public status dictionary for a provider. Raw key is strictly excluded."""
        key = self.get_raw_key(provider)
        configured = key is not None
        return {
            "provider": provider.lower(),
            "configured": configured,
            "status": "Configured" if configured else "Not Configured",
            "masked_key": mask_secret(key) if configured else None,
        }

    def get_all_providers_status(self) -> dict[str, dict[str, Any]]:
        """Return status mapping for all known candidate providers."""
        return {
            provider: self.get_provider_status(provider)
            for provider in PROVIDER_KEYS
        }

    @property
    def workflow_guidance(self) -> dict[str, Any]:
        """Return operational workflow guidance for local .env configuration (DEC-003, P02-T03)."""
        return {
            "config_method": "Local .env file edited with Notepad (DEC-003)",
            "activation": "Explicit server restart required to apply .env changes (P02-T03)",
            "hot_reload": False,
            "in_app_edit": False,
            "note": "To add, change, or remove API keys, edit your .env file with Notepad and restart the server.",
        }

    def to_public_dict(self) -> dict[str, Any]:
        """Return complete non-secret configuration dictionary for UI and diagnostic inspection.

        Secret values are never serialized.
        """
        data = self._public.model_dump()
        data["providers"] = self.get_all_providers_status()
        data["workflow_guidance"] = self.workflow_guidance
        return data

    def __repr__(self) -> str:
        return (
            f"AppConfig(env={self.app_env!r}, host={self.host!r}, "
            f"port={self.port}, default_provider={self.default_provider!r}, "
            f"secrets=<protected>)"
        )

    def __str__(self) -> str:
        return self.__repr__()


# Singleton instance accessor
_config_instance: AppConfig | None = None


def get_config(reload: bool = False, env_file: Path | str | None = None) -> AppConfig:
    """Get or initialize the global configuration instance."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = AppConfig(env_file=env_file)
    return _config_instance


def reset_config() -> None:
    """Reset global configuration singleton and clear application-managed environment variables."""
    global _config_instance
    _config_instance = None
    clear_app_managed_env()
