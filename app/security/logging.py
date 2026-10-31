"""Central structured logging baseline with redaction hooks (ADR-001, P01-T04)."""

import logging
from pathlib import Path

from app.security.masking import SecretRedactingFilter

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    known_secrets: list[str] | None = None,
) -> logging.Logger:
    """Configure root and illum loggers with secret redacting filters."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Base logger
    logger = logging.getLogger("illum")
    logger.setLevel(numeric_level)

    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    redacting_filter = SecretRedactingFilter(known_secrets=known_secrets)
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # 1. Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redacting_filter)
    logger.addHandler(console_handler)

    # 2. File handler (in logs/ if directory exists or is created)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redacting_filter)
        logger.addHandler(file_handler)

    return logger


def get_redacting_logger(name: str = "illum") -> logging.Logger:
    """Return the application logger configured with redaction filters."""
    return logging.getLogger(name)
