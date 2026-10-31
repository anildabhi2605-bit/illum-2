"""Integration tests for key add/remove and restart semantics (P02-T03, DEC-003, ACC-003)."""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from app.config import AppConfig, reset_config
from app.main import app
from app.security.env_loader import get_app_managed_keys

SENTINEL_KEY_A = "AIzaSyTestKeyAlpha0123456789abcdef9988"
SENTINEL_KEY_B = "AIzaSyTestKeyBeta9876543210fedcba1122"
SENTINEL_GROQ = "gsk_testvalid0123456789abcdef998877"


@pytest.fixture(autouse=True)
def clean_config_environment():
    """Ensure each test runs with isolated configuration and environment state."""
    reset_config()
    yield
    reset_config()


class TestConfigAddRemoveRestartSemantics:
    """Verify add, update, remove, and restart semantics for Notepad-driven .env workflow."""

    def test_add_key_and_restart_simulation(self, tmp_path: Path):
        """Verify adding a key to .env transitions provider from Not Configured to Configured upon restart."""
        env_file = tmp_path / ".env"

        # 1. Initially empty .env
        env_file.write_text("# Empty initial config\n", encoding="utf-8")
        cfg_initial = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg_initial.is_provider_configured("gemini") is False
        assert cfg_initial.get_provider_status("gemini")["status"] == "Not Configured"

        # 2. User edits .env in Notepad, adding GEMINI_API_KEY
        env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")

        # 3. Server restart (fresh AppConfig instantiation reading .env)
        cfg_restarted = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg_restarted.is_provider_configured("gemini") is True
        assert cfg_restarted.get_raw_key("gemini") == SENTINEL_KEY_A
        status = cfg_restarted.get_provider_status("gemini")
        assert status["status"] == "Configured"
        assert status["masked_key"] is not None
        assert "••••" in status["masked_key"]
        assert SENTINEL_KEY_A not in status["masked_key"]

    def test_update_key_and_restart_simulation(self, tmp_path: Path):
        """Verify modifying a key in .env updates the active key and purges the old key upon restart."""
        env_file = tmp_path / ".env"

        # 1. Initial key A
        env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")
        cfg1 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg1.get_raw_key("gemini") == SENTINEL_KEY_A

        # 2. User changes key to key B in Notepad
        env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_B}\n", encoding="utf-8")

        # 3. Server restart
        cfg2 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg2.get_raw_key("gemini") == SENTINEL_KEY_B
        assert cfg2.get_raw_key("gemini") != SENTINEL_KEY_A

    def test_remove_key_and_restart_simulation(self, tmp_path: Path):
        """Verify removing a key in .env transitions provider back to Not Configured without crash (ACC-003)."""
        env_file = tmp_path / ".env"

        # 1. Configured with Gemini and Groq
        env_file.write_text(
            f"GEMINI_API_KEY={SENTINEL_KEY_A}\nGROQ_API_KEY={SENTINEL_GROQ}\n",
            encoding="utf-8",
        )
        cfg1 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg1.is_provider_configured("gemini") is True
        assert cfg1.is_provider_configured("groq") is True

        # 2. User deletes GEMINI_API_KEY from .env in Notepad (Groq retained)
        env_file.write_text(f"GROQ_API_KEY={SENTINEL_GROQ}\n", encoding="utf-8")

        # 3. Server restart
        cfg2 = AppConfig(env_file=env_file, enforce_boundary=False)
        # Gemini is cleanly cleared
        assert cfg2.is_provider_configured("gemini") is False
        assert cfg2.get_raw_key("gemini") is None
        assert cfg2.get_provider_status("gemini")["status"] == "Not Configured"
        # Groq remains configured
        assert cfg2.is_provider_configured("groq") is True
        assert cfg2.get_raw_key("groq") == SENTINEL_GROQ

    def test_empty_or_whitespace_key_clears_configuration(self, tmp_path: Path):
        """Verify setting KEY='' or KEY='   ' in .env clears previous value and marks unconfigured."""
        env_file = tmp_path / ".env"

        # 1. Initial configured key
        env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")
        cfg1 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg1.is_provider_configured("gemini") is True

        # 2. User blanks the value in Notepad
        env_file.write_text("GEMINI_API_KEY=\n", encoding="utf-8")

        # 3. Server restart
        cfg2 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg2.is_provider_configured("gemini") is False
        assert cfg2.get_raw_key("gemini") is None
        assert cfg2.get_provider_status("gemini")["status"] == "Not Configured"

    def test_commented_out_key_treated_as_unconfigured(self, tmp_path: Path):
        """Verify commenting out # KEY=... in .env treats provider as unconfigured upon restart."""
        env_file = tmp_path / ".env"

        # 1. Configured
        env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")
        cfg1 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg1.is_provider_configured("gemini") is True

        # 2. Commented out in Notepad
        env_file.write_text(f"# GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")

        # 3. Server restart
        cfg2 = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg2.is_provider_configured("gemini") is False
        assert cfg2.get_raw_key("gemini") is None

    def test_notepad_utf8_bom_workflow(self, tmp_path: Path):
        """Verify .env saved with Windows Notepad UTF-8 BOM is cleanly parsed during restart."""
        env_file = tmp_path / ".env"

        # Windows Notepad prepends UTF-8 BOM \ufeff
        bom_content = f"\ufeffGEMINI_API_KEY={SENTINEL_KEY_A}\nGROQ_API_KEY={SENTINEL_GROQ}\n"
        env_file.write_bytes(bom_content.encode("utf-8"))

        cfg = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg.is_provider_configured("gemini") is True
        assert cfg.get_raw_key("gemini") == SENTINEL_KEY_A
        assert cfg.is_provider_configured("groq") is True
        assert cfg.get_raw_key("groq") == SENTINEL_GROQ


class TestEnvironmentIsolationAndPrecedence:
    """Verify environment isolation rules and explicit configuration precedence."""

    def test_external_env_vars_never_deleted_or_overwritten(self, tmp_path: Path):
        """Verify external system variables are completely preserved when .env changes."""
        # Inject external system environment variable
        external_key = "MY_EXTERNAL_SYSTEM_ENV_VAR"
        external_val = "important_host_system_setting_123"
        os.environ[external_key] = external_val

        try:
            env_file = tmp_path / ".env"
            # 1. Add key to .env
            env_file.write_text(f"GEMINI_API_KEY={SENTINEL_KEY_A}\n", encoding="utf-8")
            cfg1 = AppConfig(env_file=env_file, enforce_boundary=False)
            assert cfg1.is_provider_configured("gemini") is True
            assert os.environ[external_key] == external_val

            # 2. Remove key from .env and restart
            env_file.write_text("# empty\n", encoding="utf-8")
            cfg2 = AppConfig(env_file=env_file, enforce_boundary=False)
            assert cfg2.is_provider_configured("gemini") is False

            # External variable MUST still exist and remain untouched
            assert external_key in os.environ
            assert os.environ[external_key] == external_val
            # Confirm external key was never tracked as app-managed
            assert external_key not in get_app_managed_keys()

        finally:
            if external_key in os.environ:
                del os.environ[external_key]

    def test_external_port_env_precedence_over_dotenv(self, tmp_path: Path):
        """Verify external environment variable takes precedence over .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("PORT=8080\n", encoding="utf-8")

        # Set external PORT before loading
        os.environ["PORT"] = "9999"
        try:
            cfg = AppConfig(env_file=env_file, enforce_boundary=False)
            # External PORT (9999) must take precedence over .env (8080)
            assert cfg.port == 9999
            # And PORT was not claimed as an app-managed key
            assert "PORT" not in get_app_managed_keys()
        finally:
            if "PORT" in os.environ:
                del os.environ["PORT"]

    def test_raw_values_precedence_over_all(self, tmp_path: Path):
        """Verify raw_values (explicit programmatic override) takes precedence over os.environ and .env."""
        env_file = tmp_path / ".env"
        env_file.write_text("PORT=8080\n", encoding="utf-8")
        os.environ["PORT"] = "9000"

        try:
            cfg = AppConfig(
                env_file=env_file,
                raw_values={"PORT": "7777"},
                enforce_boundary=False,
            )
            assert cfg.port == 7777
        finally:
            if "PORT" in os.environ:
                del os.environ["PORT"]


class TestRestartGuidanceAndEndpoints:
    """Verify restart instructions and absence of secret leakage on runtime endpoints."""

    @pytest.mark.asyncio
    async def test_status_endpoint_returns_workflow_guidance(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.get("/api/config/status")
            assert resp.status_code == 200
            data = resp.json()

            # Verify workflow guidance is present
            assert "workflow_guidance" in data
            guidance = data["workflow_guidance"]
            assert guidance["hot_reload"] is False
            assert guidance["in_app_edit"] is False
            assert "restart" in guidance["activation"].lower()
            assert "notepad" in guidance["config_method"].lower()
            assert "restart" in guidance["note"].lower()

            # Confirm zero raw secrets
            assert "••••" in resp.text or "Not Configured" in resp.text

    def test_to_public_dict_includes_workflow_guidance(self):
        cfg = AppConfig(raw_values={"GEMINI_API_KEY": SENTINEL_KEY_A})
        public_dict = cfg.to_public_dict()
        assert "workflow_guidance" in public_dict
        assert public_dict["workflow_guidance"]["hot_reload"] is False
        assert public_dict["workflow_guidance"]["in_app_edit"] is False
        assert SENTINEL_KEY_A not in str(public_dict)
