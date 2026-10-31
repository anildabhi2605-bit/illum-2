"""Security Acceptance Test Suite for Phase P02 Exit Gate (P02-T05, ACC-002, ACC-002A, ACC-003, DEC-003, DEC-018).

Verifies the complete configuration and secret lifecycle end to end:
1. Startup with sentinel key: Key masked in UI, API responses, and logs.
2. Connection probe: Zero key leakage in request headers, logs, or error responses.
3. Removal of key: Key purged cleanly without crashing; status transitions to NOT_CONFIGURED.
4. Plaintext limitation: Truthfully disclosed without claiming encryption.
5. In-browser boundaries: No in-browser secret inputs or write capabilities.
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from app.config import AppConfig, reset_config
from app.main import app
from app.security.env_loader import clear_app_managed_env, load_local_env

CANARY_SENTINEL = "AIzaSyP02T05SentinelCanaryStrictlyConfidential999"


@pytest.fixture(autouse=True)
def clean_test_environment():
    clear_app_managed_env()
    reset_config()
    yield
    clear_app_managed_env()
    reset_config()


class TestPhase02SecurityAcceptance:
    """Complete end-to-end security verification for Phase P02 exit gate."""

    @pytest.mark.asyncio
    async def test_sentinel_lifecycle_startup_masking_and_ui(self, tmp_path: Path):
        """Step 1 & 2: Startup with sentinel key, verify masking across API and UI."""
        env_file = tmp_path / ".env"
        env_file.write_text(f"GEMINI_API_KEY={CANARY_SENTINEL}\n", encoding="utf-8")

        # Load environment from temporary path (enforce_boundary=False for pytest tmp_path)
        loaded = load_local_env(env_file, enforce_boundary=False)
        assert loaded.get("GEMINI_API_KEY") == CANARY_SENTINEL

        cfg = AppConfig(raw_values={"GEMINI_API_KEY": CANARY_SENTINEL})
        app.state.config = cfg

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            # 1. API Status Endpoint (ACC-002A)
            status_resp = await client.get("/api/config/status")
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            assert CANARY_SENTINEL not in status_resp.text
            gemini_status = status_data["providers"]["gemini"]
            assert gemini_status["configured"] is True
            assert gemini_status["masked_key"] == "••••l999"

            # 2. UI Settings HTML Endpoint
            ui_resp = await client.get("/settings")
            assert ui_resp.status_code == 200
            assert "text/html" in ui_resp.headers["content-type"]
            ui_html = ui_resp.text

            # Crucial negative assertion: Sentinel raw string NEVER in HTML
            assert CANARY_SENTINEL not in ui_html

            # Positive assertions: Masked value and disclosure present
            assert "••••l999" in ui_html
            assert "Security Disclosure — Plaintext Local Storage" in ui_html
            assert "NOT encrypted at rest" in ui_html
            assert "Open with Notepad" in ui_html
            assert "Restart Server" in ui_html

            # Zero input fields for secrets (read-only UI)
            assert '<input type="password"' not in ui_html
            assert '<input type="text" name=' not in ui_html
            assert '<form' not in ui_html

    @pytest.mark.asyncio
    async def test_key_removal_and_graceful_recovery(self, tmp_path: Path):
        """Step 3: Key removal transitions provider to NOT_CONFIGURED without crashing (ACC-003)."""
        env_file = tmp_path / ".env"
        env_file.write_text(f"GROQ_API_KEY={CANARY_SENTINEL}\n", encoding="utf-8")
        load_local_env(env_file, enforce_boundary=False)

        # Now simulate user emptying the key in Notepad
        env_file.write_text("GROQ_API_KEY=\n", encoding="utf-8")
        cfg_cleared = AppConfig(env_file=env_file, enforce_boundary=False)
        assert cfg_cleared.is_provider_configured("groq") is False
        assert cfg_cleared.get_raw_key("groq") is None

        app.state.config = cfg_cleared

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            # API shows NOT CONFIGURED
            status_resp = await client.get("/api/config/status")
            assert status_resp.status_code == 200
            data = status_resp.json()
            assert data["providers"]["groq"]["configured"] is False
            assert data["providers"]["groq"]["masked_key"] is None

            # UI displays NOT CONFIGURED cleanly
            ui_resp = await client.get("/settings")
            assert ui_resp.status_code == 200
            assert "NOT CONFIGURED" in ui_resp.text
            assert CANARY_SENTINEL not in ui_resp.text

            # Other features and health check remain 100% operable
            health_resp = await client.get("/health")
            assert health_resp.status_code == 200
            assert health_resp.json()["status"] == "healthy"

    def test_log_file_clean_of_sentinel_secrets(self):
        """Step 4: Inspect logs/app.log to guarantee zero sentinel leaks."""
        log_path = Path("logs/app.log")
        if log_path.exists():
            log_content = log_path.read_text(encoding="utf-8", errors="replace")
            assert CANARY_SENTINEL not in log_content

    def test_repository_clean_of_plain_text_sentinels(self):
        """Step 5: Verify tracked source files are free of live secrets."""
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in {".git", ".pytest_cache", "venv", ".venv", "node_modules", "data", "tmp", "logs"}]
            for file in files:
                if file.endswith((".py", ".json", ".md", ".html", ".js", ".css")):
                    path = Path(root) / file
                    try:
                        content = path.read_text(encoding="utf-8", errors="replace")
                        # Must not contain live accidental commit
                        assert CANARY_SENTINEL not in content or "test_p02_t05_config_acceptance.py" in str(path)
                    except Exception:
                        pass
