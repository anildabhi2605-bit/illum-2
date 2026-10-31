"""Unit tests for UI secret status rendering and template safety (P02-T05, ADR-001, DEC-003)."""
from __future__ import annotations

from starlette.requests import Request

from app.config import AppConfig
from app.ui.routes import build_provider_ui_models, templates

CANARY_GEMINI = "AIzaSyTestCanaryGemini0123456789abcdef"
CANARY_GROQ = "gsk_testCanaryGroq0123456789abcdef99"


class TestUISecretRenderingSafety:
    """Verify that UI data models and rendered HTML never expose unmasked secrets."""

    def test_build_provider_ui_models_includes_all_four_providers(self):
        config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": CANARY_GEMINI,
                "GROQ_API_KEY": CANARY_GROQ,
            }
        )
        models = build_provider_ui_models(config)
        assert len(models) == 4

        provider_ids = [m["id"] for m in models]
        assert "gemini" in provider_ids
        assert "groq" in provider_ids
        assert "openai" in provider_ids
        assert "openrouter" in provider_ids

    def test_build_provider_ui_models_strictly_masks_secrets(self):
        config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": CANARY_GEMINI,
                "GROQ_API_KEY": CANARY_GROQ,
            }
        )
        models = build_provider_ui_models(config)
        gemini_model = next(m for m in models if m["id"] == "gemini")
        groq_model = next(m for m in models if m["id"] == "groq")
        openai_model = next(m for m in models if m["id"] == "openai")

        # Configured providers
        assert gemini_model["configured"] is True
        assert gemini_model["masked_key"] == "••••cdef"
        assert CANARY_GEMINI not in repr(gemini_model)

        assert groq_model["configured"] is True
        assert groq_model["masked_key"] == "••••ef99"
        assert CANARY_GROQ not in repr(groq_model)

        # Unconfigured provider
        assert openai_model["configured"] is False
        assert openai_model["masked_key"] is None

    def test_template_rendering_never_leaks_secrets_in_html(self):
        config = AppConfig(
            raw_values={
                "GEMINI_API_KEY": CANARY_GEMINI,
                "GROQ_API_KEY": CANARY_GROQ,
            }
        )
        providers = build_provider_ui_models(config)

        # Create dummy starlette request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/settings",
            "headers": [],
        }
        request = Request(scope)

        response = templates.TemplateResponse(
            "settings.html",
            {
                "request": request,
                "version": "0.1.0",
                "port": 8000,
                "providers": providers,
                "app_env": "development",
            },
        )

        html = response.body.decode("utf-8")

        # Canary secrets must NEVER appear anywhere in the rendered HTML
        assert CANARY_GEMINI not in html
        assert CANARY_GROQ not in html

        # Masked values must appear
        assert "••••cdef" in html
        assert "••••ef99" in html

        # Plaintext warning must appear
        assert "Plaintext Local Storage" in html
        assert "NOT encrypted at rest" in html

        # Notepad workflow must appear
        assert "Open with Notepad" in html
        assert "Restart Server" in html

        # Buttons must exist with data-provider
        assert 'data-provider="gemini"' in html
        assert 'data-provider="groq"' in html
        assert 'data-provider="openai"' in html
        assert 'data-provider="openrouter"' in html
        assert 'id="btn-test-all"' in html

        # Zero input fields for secrets
        assert '<input type="password"' not in html
        assert '<input type="text" name="api_key"' not in html
