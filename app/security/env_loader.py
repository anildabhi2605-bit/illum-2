"""Strict local .env file loader with missing-file fallback and security boundary checks.

ADR-001 / P02-T01 / CONFIG_AND_SECRETS_SPEC:
- Strictly loads local .env within project root boundary; rejects remote or traversal paths.
- Missing-file fallback: returns empty dict / defaults if .env is absent without crashing.
- Empty file fallback: gracefully handles empty or comment-only .env.
- UTF-8 with BOM tolerance (Windows Notepad workflow).
- Sanitized parsing: never leaks secret contents in warnings or error traces.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Root directory of the repository
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Set of environment variable keys set by the application from local .env
_APP_MANAGED_ENV_KEYS: set[str] = set()


def get_app_managed_keys() -> set[str]:
    """Return a copy of the keys currently tracked as set by the application from .env."""
    return set(_APP_MANAGED_ENV_KEYS)


def clear_app_managed_env(target_keys: set[str] | None = None) -> set[str]:
    """Clear only the environment variables previously set by the application from .env.

    Guarantees unrelated external/system environment variables are never touched or deleted.

    Returns:
        The set of keys that were removed from os.environ.
    """
    global _APP_MANAGED_ENV_KEYS
    keys_to_clear = (
        set(_APP_MANAGED_ENV_KEYS)
        if target_keys is None
        else (set(_APP_MANAGED_ENV_KEYS) & target_keys)
    )
    cleared = set()
    for k in keys_to_clear:
        if k in os.environ:
            del os.environ[k]
            cleared.add(k)
        _APP_MANAGED_ENV_KEYS.discard(k)
    return cleared


class EnvPathSecurityError(ValueError):
    """Raised when an attempt is made to load a .env file outside approved local project boundaries."""

    pass


class EnvParseError(ValueError):
    """Raised when .env syntax is fatally corrupted."""

    pass


def resolve_local_env_path(
    env_file: Path | str | None = None,
    project_root: Path | None = None,
    enforce_boundary: bool = True,
) -> Path:
    """Resolve and validate the local .env file path within the project root.

    Prevents directory traversal and loading arbitrary or remote configuration paths.
    """
    root = (project_root or DEFAULT_PROJECT_ROOT).resolve()

    if env_file is None:
        target_path = root / ".env"
    else:
        target_path = Path(env_file).resolve()

    if enforce_boundary:
        try:
            target_path.relative_to(root)
        except ValueError:
            raise EnvPathSecurityError(
                f"Security violation: path traversal detected. "
                f"Target path '{target_path.name}' must reside within project root."
            )

    return target_path


def parse_env_content(content: str) -> dict[str, str]:
    """Parse .env content safely.

    Handles:
    - UTF-8 BOM
    - Comment lines (#)
    - Empty lines
    - Leading/trailing whitespace
    - Quoted values (single or double quotes)
    - Ignores malformed lines safely without echoing their contents
    """
    parsed: dict[str, str] = {}
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            # Line is malformed; log sanitized warning without printing line contents
            logger.warning(
                "Skipping malformed line %d in .env: missing '=' separator.",
                line_num,
            )
            continue

        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()

        if not key:
            logger.warning("Skipping empty key on line %d in .env.", line_num)
            continue

        # Strip surrounding matching quotes
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]

        parsed[key] = val

    return parsed


def load_local_env(
    env_file: Path | str | None = None,
    project_root: Path | None = None,
    apply_to_environ: bool = True,
    override: bool = False,
    enforce_boundary: bool = True,
) -> dict[str, str]:
    """Load and parse local .env file with missing-file and empty-file fallbacks.

    Returns parsed key-value mapping. Never crashes when .env does not exist.
    """
    target_path = resolve_local_env_path(
        env_file=env_file,
        project_root=project_root,
        enforce_boundary=enforce_boundary,
    )

    if not target_path.exists():
        logger.info(
            "Local .env file not found at '%s'. Falling back to default configuration with unconfigured providers.",
            target_path.name,
        )
        if apply_to_environ:
            # Missing .env on startup/restart must clear previously loaded app-managed keys
            clear_app_managed_env()
        return {}

    try:
        content = target_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        logger.error("Failed to read '%s': file is not valid UTF-8.", target_path.name)
        raise EnvParseError(f"File '{target_path.name}' is not valid UTF-8.")
    except Exception as exc:
        logger.error("Failed to access '%s': %s", target_path.name, type(exc).__name__)
        raise

    parsed = parse_env_content(content)

    if apply_to_environ:
        global _APP_MANAGED_ENV_KEYS

        # 1. Purge previously app-managed keys that were removed or emptied in the new .env
        stale_keys = {
            k
            for k in _APP_MANAGED_ENV_KEYS
            if k not in parsed or not parsed[k].strip()
        }
        for k in stale_keys:
            if k in os.environ:
                del os.environ[k]
            _APP_MANAGED_ENV_KEYS.discard(k)

        # 2. Ingest current .env keys with strict environment isolation
        for k, v in parsed.items():
            clean_val = v.strip()
            if not clean_val:
                # Key explicitly empty in .env: ensure cleared if previously app-managed
                if k in _APP_MANAGED_ENV_KEYS:
                    if k in os.environ:
                        del os.environ[k]
                    _APP_MANAGED_ENV_KEYS.discard(k)
                continue

            # If key is already in os.environ but was NOT set by the app, preserve external env
            if k in os.environ and k not in _APP_MANAGED_ENV_KEYS and not override:
                continue

            # Load into os.environ and record as app-managed
            os.environ[k] = clean_val
            _APP_MANAGED_ENV_KEYS.add(k)

    return parsed
