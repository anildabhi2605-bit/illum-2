"""Integration tests for UI endpoints, static assets, and content negotiation (P02-T05, ADR-001)."""
from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from app.config import AppConfig, reset_config
from app.main import app

CANARY_KEY = "AIzaSyTestIntegrationCanary9876543210zyx"


@pytest.fixture(autouse=True)
def clean_config():
    reset_config()
    yield
    reset_config()


class TestUIEndpointsIntegration:
    """Verify HTML routes, static assets, and content negotiation."""

    @pytest.mark.asyncio
    async def test_get_settings_page_returns_html(self):
        app.state.config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": CANARY_KEY,
            }
        )

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.get("/settings")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]

            html = resp.text
            assert "ILLUM AI STUDIO" in html
            assert "Provider Configuration & Status" in html
            assert "Plaintext Local Storage" in html
            assert "Restart Required" in html or "Restart Server" in html

            # Masked key is present; CANARY is never present
            assert "••••10zyx" in html or "••••0zyx" in html or "••••" in html
            assert CANARY_KEY not in html

    @pytest.mark.asyncio
    async def test_get_config_ui_alias_returns_html(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.get("/config-ui")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_static_js_asset_served_properly(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            resp = await client.get("/static/js/config_status.js")
            assert resp.status_code == 200
            assert "testSingleProvider" in resp.text
            assert "btn-test-all" in resp.text

    @pytest.mark.asyncio
    async def test_root_content_negotiation(self):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            # 1. Default / JSON client
            resp_json = await client.get("/", headers={"Accept": "application/json"})
            assert resp_json.status_code == 200
            assert "application/json" in resp_json.headers["content-type"]
            data = resp_json.json()
            assert data["status"] == "online"
            assert data["app"] == "ILLUM AI STUDIO"

            # 2. Browser request with text/html
            resp_html = await client.get(
                "/",
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            )
            assert resp_html.status_code == 200
            assert "text/html" in resp_html.headers["content-type"]
            assert "Provider Configuration & Status" in resp_html.text
