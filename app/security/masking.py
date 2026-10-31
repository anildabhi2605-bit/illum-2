"""Secret masking and log redaction utilities (DEC-003, DEC-018, ACC-002A)."""

import logging
import re
from collections.abc import Iterable

# Regex patterns matching common API keys and secret bearer tokens
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),               # Google API Key / Gemini
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                 # OpenAI / generic secret key
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),                # Groq API Key
    re.compile(r"Bearer\s+[A-Za-z0-9-._~+/]+=*", re.IGNORECASE),  # Bearer token
    re.compile(r"illum_sentinel_[A-Za-z0-9_]+"),        # Sentinel test keys
    re.compile(r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?([A-Za-z0-9-_]{8,})['\"]?", re.IGNORECASE),
]


def mask_secret(secret: str | None, visible_suffix_len: int = 4) -> str | None:
    """Return a masked representation of a secret string (e.g., '••••12a4').

    Never returns the raw secret. If the secret is None or empty, returns None.
    """
    if not secret:
        return None

    secret_str = str(secret).strip()
    if not secret_str:
        return None

    if len(secret_str) <= visible_suffix_len:
        return "••••••••"

    return "••••" + secret_str[-visible_suffix_len:]


def is_masked(val: str | None) -> bool:
    """Return True if the value appears to be a masked secret."""
    if not val or not isinstance(val, str):
        return False
    return val.startswith("••••")


def redact_text(text: str, custom_secrets: Iterable[str] | None = None) -> str:
    """Scrub known secret patterns and custom secret values from text."""
    if not text:
        return ""

    result = str(text)

    # Redact custom known secrets if provided
    if custom_secrets:
        for secret in custom_secrets:
            if secret and len(secret) > 3:
                result = result.replace(secret, "[REDACTED_SECRET]")

    # Redact via regex patterns
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED_SECRET]", result)

    return result


class SecretRedactingFilter(logging.Filter):
    """Logging filter that redacts secrets and sensitive payloads from all log records."""

    def __init__(self, known_secrets: list[str] | None = None):
        super().__init__()
        self.known_secrets = known_secrets or []

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg, self.known_secrets)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_text(v, self.known_secrets) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_text(a, self.known_secrets) if isinstance(a, str) else a
                    for a in record.args
                )

        return True
