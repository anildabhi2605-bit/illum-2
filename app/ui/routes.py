"""UI routes and template rendering for ILLUM AI STUDIO desktop runtime (P02-T05, ADR-001).

Governed by:
- ADR-001: Embedded localhost web UI using Jinja2 + HTML5 + Tailwind + Vanilla JS.
- Zero Node.js or npm dependencies for end-user execution.
- DEC-003: Plaintext .env disclosure & Notepad workflow guidance.
- Secret safety: Raw keys NEVER exposed in template context or HTML.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import get_config

router = APIRouter(tags=["UI"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def build_provider_ui_models(cfg: Any) -> list[dict[str, Any]]:
    """Build sanitized view models for the 4 providers.
    
    Invariants:
    - Never include raw API keys.
    - Only include masked key values (••••cdef) or None.
    - Accurately reflect configuration status.
    """
    provider_meta = {
        "gemini": {
            "name": "Google Gemini",
            "icon": "✨",
            "role": "Candidate Script, Prompt & Vision Engine",
            "env_var": "GEMINI_API_KEY",
            "auth_endpoint": "GET /v1beta/models",
        },
        "groq": {
            "name": "Groq",
            "icon": "⚡",
            "role": "Ultra-Fast Inference (Llama 3 / Mixtral)",
            "env_var": "GROQ_API_KEY",
            "auth_endpoint": "GET /openai/v1/models",
        },
        "openai": {
            "name": "OpenAI",
            "icon": "🧠",
            "role": "GPT-4o / Reasoning / Embeddings",
            "env_var": "OPENAI_API_KEY",
            "auth_endpoint": "GET /v1/models",
        },
        "openrouter": {
            "name": "OpenRouter",
            "icon": "🌐",
            "role": "Multi-Provider Router & Backup",
            "env_var": "OPENROUTER_API_KEY",
            "auth_endpoint": "GET /v1/models",
        },
    }

    all_status = cfg.get_all_providers_status()
    models = []
    for pid, meta in provider_meta.items():
        st = all_status.get(pid, {})
        models.append({
            "id": pid,
            "name": meta["name"],
            "icon": meta["icon"],
            "role": meta["role"],
            "env_var": meta["env_var"],
            "auth_endpoint": meta["auth_endpoint"],
            "configured": st.get("configured", False),
            "masked_key": st.get("masked_key"),
        })
    return models


@router.get("/settings", response_class=HTMLResponse)
@router.get("/config-ui", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    """Render Provider Configuration & Secret Status page."""
    cfg = getattr(request.app.state, "config", get_config())
    port = getattr(request.app.state, "port", 8000)
    providers = build_provider_ui_models(cfg)

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "version": __version__,
            "port": port,
            "providers": providers,
            "app_env": cfg.app_env,
        },
    )
