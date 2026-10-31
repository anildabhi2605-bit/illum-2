"""Unit tests for typed configuration loading, strict local .env loader, and secret safety (P02-T01)."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import (
    AllowedProvider,
    AppConfig,
    AppEnv,
    ConfigValidationError,
    LogLevel,
    get_config,
)
from app.security.env_loader import (
    EnvPathSecurityError,
    load_local_env,
    parse_env_content,
    resolve_local_env_path,
)


class TestStrictLocalEnvLoader:
    """Tests for local .env loader, missing-file fallback, and security boundaries."""

    def test_missing_file_fallback_returns_empty_dict(self, tmp_path: Path):
        """Verify missing .env does not raise an exception and returns empty dict."""
        non_existent = tmp_path / ".env"
        assert not non_existent.exists()

        result = load_local_env(
            env_file=non_existent,
            project_root=tmp_path,
            apply_to_environ=False,
        )
        assert result == {}

    def test_empty_env_file_handling(self, tmp_path: Path):
        """Verify empty or whitespace-only .env loads cleanly without error."""
        empty_file = tmp_path / ".env"
        empty_file.write_text("   \n\n   \n", encoding="utf-8")

        result = load_local_env(
            env_file=empty_file,
            project_root=tmp_path,
            apply_to_environ=False,
        )
        assert result == {}

    def test_comment_only_env_file(self, tmp_path: Path):
        """Verify comment-only .env loads without adding any keys."""
        comment_file = tmp_path / ".env"
        comment_file.write_text("# This is a comment\n# Another comment\n", encoding="utf-8")

        result = load_local_env(
            env_file=comment_file,
            project_root=tmp_path,
            apply_to_environ=False,
        )
        assert result == {}

    def test_parse_env_content_directly(self):
        """Verify parse_env_content correctly parses raw string content."""
        content = "KEY1=val1\nKEY2='val2'\nKEY3=\"val3\"\n# comment\n"
        parsed = parse_env_content(content)
        assert parsed == {"KEY1": "val1", "KEY2": "val2", "KEY3": "val3"}

    def test_notepad_workflow_utf8_bom_and_quoting(self, tmp_path: Path):
        """Verify Windows Notepad UTF-8 BOM, quoted values, and whitespace handling."""
        notepad_env = tmp_path / ".env"
        # Prepend UTF-8 BOM (\ufeff) commonly written by Windows Notepad
        content = (
            "\ufeff# Windows Notepad edited file\n"
            'PORT="8080"\n'
            "HOST='127.0.0.1'\n"
            "APP_ENV = development \n"
            'OPENAI_API_KEY="sk-activeTest1234567890abcdef"\n'
            "EMPTY_VAL=\n"
        )
        notepad_env.write_text(content, encoding="utf-8-sig")

        parsed = load_local_env(
            env_file=notepad_env,
            project_root=tmp_path,
            apply_to_environ=False,
        )

        assert parsed["PORT"] == "8080"
        assert parsed["HOST"] == "127.0.0.1"
        assert parsed["APP_ENV"] == "development"
        assert parsed["OPENAI_API_KEY"] == "sk-activeTest1234567890abcdef"
        assert parsed["EMPTY_VAL"] == ""

    def test_malformed_lines_handled_safely(self, tmp_path: Path):
        """Verify malformed lines without '=' are skipped safely without exposing data."""
        malformed_env = tmp_path / ".env"
        malformed_env.write_text(
            "VALID_KEY=valid_val\n"
            "THIS IS NOT A VALID LINE\n"
            "=VALUE_WITHOUT_KEY\n"
            "ANOTHER_VALID=123\n",
            encoding="utf-8",
        )

        parsed = load_local_env(
            env_file=malformed_env,
            project_root=tmp_path,
            apply_to_environ=False,
        )

        assert parsed == {"VALID_KEY": "valid_val", "ANOTHER_VALID": "123"}

    def test_path_traversal_boundary_security(self, tmp_path: Path):
        """Verify attempting to load .env outside project boundary raises security error."""
        outside_path = tmp_path.parent / "unauthorized.env"

        with pytest.raises(EnvPathSecurityError, match="path traversal detected"):
            resolve_local_env_path(
                env_file=outside_path,
                project_root=tmp_path,
                enforce_boundary=True,
            )


class TestTypedAppConfig:
    """Tests for typed configuration validation and public vs secret separation."""

    def test_app_config_with_missing_env_uses_safe_defaults(self, tmp_path: Path):
        """Verify AppConfig falls back to validated defaults when .env is absent."""
        clean_env = {
            "GEMINI_API_KEY": "",
            "GROQ_API_KEY": "",
            "OPENAI_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            "PORT": "8000",
            "APP_ENV": "development",
            "DEFAULT_PROVIDER": "gemini",
        }
        with patch.dict(os.environ, clean_env, clear=False):
            cfg = AppConfig(env_file=tmp_path / ".env", project_root=tmp_path)

            assert cfg.app_env == AppEnv.DEVELOPMENT.value
            assert cfg.host == "127.0.0.1"
            assert cfg.port == 8000
            assert cfg.default_provider == AllowedProvider.GEMINI.value
            assert cfg.default_model == "gemini-1.5-flash"
            assert cfg.log_level == LogLevel.INFO.value

            # All providers unconfigured
            for prov in ["gemini", "groq", "openai", "openrouter"]:
                assert cfg.is_provider_configured(prov) is False
                assert cfg.get_raw_key(prov) is None
                status = cfg.get_provider_status(prov)
                assert status["configured"] is False
                assert status["status"] == "Not Configured"
                assert status["masked_key"] is None

    def test_app_config_valid_custom_settings(self, tmp_path: Path):
        """Verify AppConfig parses and validates valid custom settings."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "PORT=9000\n"
            "HOST=127.0.0.1\n"
            "APP_ENV=production\n"
            "DEFAULT_PROVIDER=openai\n"
            "DEFAULT_MODEL=gpt-4o-mini\n"
            "LOG_LEVEL=WARNING\n"
            "OPENAI_API_KEY=sk-test-live-key-1234567890abcdef\n",
            encoding="utf-8",
        )

        cfg = AppConfig(
            env_file=env_file,
            project_root=tmp_path,
            raw_values={
                "PORT": "9000",
                "HOST": "127.0.0.1",
                "APP_ENV": "production",
                "DEFAULT_PROVIDER": "openai",
                "DEFAULT_MODEL": "gpt-4o-mini",
                "LOG_LEVEL": "WARNING",
                "OPENAI_API_KEY": "sk-test-live-key-1234567890abcdef",
            },
        )

        assert cfg.port == 9000
        assert cfg.host == "127.0.0.1"
        assert cfg.app_env == "production"
        assert cfg.default_provider == "openai"
        assert cfg.default_model == "gpt-4o-mini"
        assert cfg.log_level == "WARNING"

        assert cfg.is_provider_configured("openai") is True
        assert cfg.get_raw_key("openai") == "sk-test-live-key-1234567890abcdef"
        status = cfg.get_provider_status("openai")
        assert status["configured"] is True
        assert status["status"] == "Configured"
        assert status["masked_key"] == "••••cdef"

    def test_invalid_port_raises_sanitized_error(self):
        """Verify non-integer PORT raises a sanitized ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Invalid configuration for PORT"):
            AppConfig(raw_values={"PORT": "invalid_port"})

    def test_invalid_app_env_raises_sanitized_error(self):
        """Verify invalid APP_ENV enum raises a sanitized ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Invalid configuration for APP_ENV"):
            AppConfig(raw_values={"APP_ENV": "super_production"})

    def test_invalid_default_provider_raises_sanitized_error(self):
        """Verify unsupported default provider enum raises a sanitized ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Invalid configuration for DEFAULT_PROVIDER"):
            AppConfig(raw_values={"DEFAULT_PROVIDER": "unsupported_ai_vendor"})

    def test_invalid_log_level_raises_sanitized_error(self):
        """Verify invalid log level raises a sanitized ConfigValidationError."""
        with pytest.raises(ConfigValidationError, match="Invalid configuration for LOG_LEVEL"):
            AppConfig(raw_values={"LOG_LEVEL": "SUPER_VERBOSE"})


class TestSentinelSecretRedaction:
    """Security verification ensuring secrets are never serialized or leaked."""

    SENTINEL_SECRET = "sk-test-SENTINEL-SECRET-KEY-xyz1234567890abcdef"

    def test_sentinel_never_serialized_in_public_dict(self):
        """Verify to_public_dict() contains zero raw secrets."""
        cfg = AppConfig(
            raw_values={
                "OPENAI_API_KEY": self.SENTINEL_SECRET,
                "GEMINI_API_KEY": "gemini-sentinel-another-secret-key-9999",
            }
        )

        public_dict = cfg.to_public_dict()
        serialized = str(public_dict)

        assert self.SENTINEL_SECRET not in serialized
        assert "gemini-sentinel-another-secret-key-9999" not in serialized
        assert "SENTINEL-SECRET-KEY" not in serialized

        # Providers show masked representation only
        assert public_dict["providers"]["openai"]["masked_key"] == "••••cdef"
        assert public_dict["providers"]["gemini"]["masked_key"] == "••••9999"

    def test_sentinel_never_in_string_representations(self):
        """Verify string representations of AppConfig and ProviderSecrets never leak keys."""
        cfg = AppConfig(raw_values={"OPENAI_API_KEY": self.SENTINEL_SECRET})

        assert self.SENTINEL_SECRET not in str(cfg)
        assert self.SENTINEL_SECRET not in repr(cfg)
        assert self.SENTINEL_SECRET not in str(cfg.secrets)
        assert self.SENTINEL_SECRET not in repr(cfg.secrets)
        assert "<protected>" in repr(cfg.secrets)

    def test_singleton_accessor(self):
        """Verify get_config singleton returns stable instance and reloads on demand."""
        cfg1 = get_config(reload=True)
        cfg2 = get_config(reload=False)
        assert cfg1 is cfg2
