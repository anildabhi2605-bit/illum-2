"""Security tests: Secret masking, redaction, and traceback sanitization (ACC-002A, DEC-003)."""

import io
import logging
import os
import unittest
from typing import ClassVar
from unittest.mock import patch

import httpx

from app.main import app, lifespan
from app.security.masking import SecretRedactingFilter, mask_secret, redact_text


class TestSecretMasking(unittest.IsolatedAsyncioTestCase):
    """Test suite validating secret masking and log redaction invariants (ACC-002A)."""

    SENTINEL_KEYS: ClassVar[list[str]] = [
        "AIzaSyD-TEST-GEMINI-KEY-1234567890abcdef",
        "sk-testOpenAIKey9876543210abcdefghijklmnop",
        "gsk_testGroqKey1234567890abcdefghijklmnop",
        "illum_sentinel_secret_test_key_xyz123",
    ]

    def test_mask_secret_formatting(self):
        """Verify mask_secret only exposes visible suffix and never full key."""
        for key in self.SENTINEL_KEYS:
            masked = mask_secret(key, visible_suffix_len=4)
            self.assertIsNotNone(masked)
            self.assertTrue(masked.startswith("••••"))
            self.assertEqual(masked[-4:], key[-4:])
            self.assertNotIn(key, masked)

    def test_mask_secret_empty_and_short(self):
        """Verify empty and short key handling."""
        self.assertIsNone(mask_secret(None))
        self.assertIsNone(mask_secret(""))
        self.assertEqual(mask_secret("abc"), "••••••••")

    def test_redact_text_scrubs_sentinel_patterns(self):
        """Verify redact_text scrubs standard key patterns."""
        for key in self.SENTINEL_KEYS:
            sample_text = f"Connecting to provider with key={key} in session"
            redacted = redact_text(sample_text)
            self.assertNotIn(key, redacted)
            self.assertIn("[REDACTED_SECRET]", redacted)

    def test_logger_filter_redacts_secrets_from_records(self):
        """Verify SecretRedactingFilter scrubs raw keys from log output."""
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.addFilter(SecretRedactingFilter(known_secrets=self.SENTINEL_KEYS))
        handler.setFormatter(logging.Formatter("%(message)s"))

        test_logger = logging.getLogger("test_redaction_logger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(handler)

        test_logger.info("Attempting provider authentication with %s", self.SENTINEL_KEYS[0])
        test_logger.warning("Authentication failed for key %s", self.SENTINEL_KEYS[1])

        output = log_stream.getvalue()
        for key in self.SENTINEL_KEYS[:2]:
            self.assertNotIn(key, output, f"Raw secret {key} leaked in log output!")
        self.assertIn("[REDACTED_SECRET]", output)

    async def test_api_config_status_masks_configured_keys(self):
        """Verify /api/config/status returns masked key and never raw key (ACC-002A)."""
        test_env = {
            "GEMINI_API_KEY": "AIzaSyD-TEST-GEMINI-KEY-1234567890abcdef",
            "OPENAI_API_KEY": "sk-testOpenAIKey9876543210abcdefghijklmnop",
        }
        with patch.dict(os.environ, test_env, clear=False):
            async with lifespan(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8000",
            ) as client:
                response = await client.get("/api/config/status")
                self.assertEqual(response.status_code, 200)

                data = response.json()
                providers = data.get("providers", {})

                gemini = providers.get("gemini", {})
                self.assertTrue(gemini.get("configured"))
                self.assertEqual(gemini.get("status"), "Configured")
                self.assertEqual(gemini.get("masked_key"), "••••cdef")

                openai = providers.get("openai", {})
                self.assertTrue(openai.get("configured"))
                self.assertEqual(openai.get("status"), "Configured")
                self.assertEqual(openai.get("masked_key"), "••••mnop")

                # Verify raw keys NEVER exist anywhere in the payload
                payload_str = str(data)
                for key in test_env.values():
                    self.assertNotIn(key, payload_str, "Raw API key found in API response!")


if __name__ == "__main__":
    unittest.main()
