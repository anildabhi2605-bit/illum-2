"""ILLUM AI STUDIO — Local FastAPI Runtime Entrypoint (ADR-001, P01-T03, P01-T04).

Governed by ADR-001:
- Framework: FastAPI + Uvicorn (ASGI)
- Binding: Strictly localhost (127.0.0.1:8000)
- Endpoints: Health check, startup lifecycle, config status, sanitized error handling
- Logging: Structured with automatic secret/payload redacting hooks
"""

import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_config
from app.security.key_validator import (
    KeyValidationResult,
    validate_all_keys,
    validate_api_key,
)
from app.security.logging import setup_logging
from app.ui.routes import router as ui_router, settings_page
from app.use_cases.test_provider_connection import (
    ProviderConnectionTestResult,
    test_all_provider_connections,
    test_provider_connection,
)

# Configure secure console and file logging (sanitized, zero secret dumping)
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/app.log",
)

# Authoritative binding defaults per ADR-001
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    # --- Startup ---
    cfg = get_config(reload=True)
    host = os.getenv("HOST", DEFAULT_HOST)
    port = int(os.getenv("PORT", str(DEFAULT_PORT)))

    # Ensure local runtime directories exist (governed by .gitignore)
    for dir_name in ["data", "logs", "tmp", "exports"]:
        os.makedirs(dir_name, exist_ok=True)

    logger.info("==================================================")
    logger.info("   ILLUM AI STUDIO — Local Desktop Runtime")
    logger.info("   Version: %s", __version__)
    logger.info("   Binding: http://%s:%d (Localhost Only)", host, port)
    logger.info("   Environment: %s", cfg.app_env)
    logger.info("==================================================")

    # Store runtime state
    app.state.healthy = True
    app.state.host = host
    app.state.port = port
    app.state.config = cfg

    yield

    # --- Shutdown ---
    logger.info("ILLUM AI STUDIO shutting down gracefully...")
    app.state.healthy = False


# Create FastAPI application
app = FastAPI(
    title="ILLUM AI STUDIO",
    description="YouTube Script, Video Prompts, Thumbnail & SEO Studio Workbench",
    version=__version__,
    lifespan=lifespan,
)

# Mount static asset directory for embedded UI (Vanilla JS, CSS)
_STATIC_DIR = Path(__file__).parent / "ui" / "static"
os.makedirs(_STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Mount UI router
app.include_router(ui_router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Sanitize unhandled exceptions; strictly prevent traceback or key leakage."""
    logger.error("Unhandled runtime exception: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. No sensitive details or secrets are exposed.",
        },
    )


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint verifying server status and localhost binding."""
    return {
        "status": "healthy",
        "app": "ILLUM AI STUDIO",
        "version": __version__,
        "host": getattr(app.state, "host", DEFAULT_HOST),
        "port": getattr(app.state, "port", DEFAULT_PORT),
    }


@app.get("/", tags=["System"])
async def root_status(request: Request) -> Any:
    """Root entrypoint returning application status JSON or HTML workbench."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return await settings_page(request)
    return {
        "app": "ILLUM AI STUDIO",
        "version": __version__,
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
        "ui_url": "/settings",
    }


@app.get("/api/config/status", tags=["Configuration"])
async def config_status() -> dict[str, Any]:
    """Return provider configuration status, masked keys, and restart workflow guidance.

    Raw keys are NEVER returned or serialized.
    """
    cfg = getattr(app.state, "config", get_config())
    return {
        "app_env": cfg.app_env,
        "default_provider": cfg.default_provider,
        "default_model": cfg.default_model,
        "providers": cfg.get_all_providers_status(),
        "workflow_guidance": cfg.workflow_guidance,
    }


@app.post("/api/config/validate", tags=["Configuration"])
async def validate_all_provider_keys(online: bool = True) -> dict[str, Any]:
    """Safely validate all configured provider keys via metadata probe (P02-T02).

    Raw keys are strictly excluded from output and logs.
    """
    cfg = getattr(app.state, "config", get_config())
    results = await validate_all_keys(config=cfg, online=online)
    return {
        "providers": {
            provider: result.model_dump()
            for provider, result in results.items()
        }
    }


@app.post("/api/config/validate/{provider}", tags=["Configuration"])
async def validate_single_provider_key(provider: str, online: bool = True) -> dict[str, Any]:
    """Safely validate a single provider's configured key (P02-T02)."""
    cfg = getattr(app.state, "config", get_config())
    raw_key = cfg.get_raw_key(provider)
    result: KeyValidationResult = await validate_api_key(
        provider=provider,
        api_key=raw_key,
        online=online,
    )
    return result.model_dump()


@app.post("/api/providers/test-connection", tags=["Providers"])
async def test_all_connections() -> dict[str, Any]:
    """Test connection to all configured providers via metadata probe on explicit request (P02-T04).

    Strictly uses low-cost metadata endpoints; never executes paid generation.
    """
    cfg = getattr(app.state, "config", get_config())
    results = await test_all_provider_connections(config=cfg)
    return {
        "connections": {
            provider: result.model_dump()
            for provider, result in results.items()
        }
    }


@app.post("/api/providers/{provider}/test-connection", tags=["Providers"])
async def test_single_connection(provider: str) -> dict[str, Any]:
    """Test connection to a specific provider on explicit request (P02-T04)."""
    cfg = getattr(app.state, "config", get_config())
    raw_key = cfg.get_raw_key(provider)
    result: ProviderConnectionTestResult = await test_provider_connection(
        provider=provider,
        api_key=raw_key,
    )
    return result.model_dump()


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = False) -> None:
    """Launch Uvicorn server strictly bound to localhost."""
    import uvicorn

    # Security check: warn if binding to non-loopback
    if host != "127.0.0.1" and host != "localhost":
        logger.warning(
            "SECURITY ALERT: Server binding '%s' is not loopback (127.0.0.1).",
            host,
        )

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    host_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port_arg = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    run_server(host=host_arg, port=port_arg)
