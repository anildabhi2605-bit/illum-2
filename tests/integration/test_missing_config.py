"""Integration tests: Missing configuration and key removal handling (ACC-003, ADR-001)."""

import os
import unittest
from unittest.mock import patch

import httpx

from app.config import PROVIDER_KEYS, AppConfig
from app.main import app, lifespan


class TestMissingConfig(unittest.IsolatedAsyncioTestCase):
    """Test suite validating application behavior when API keys or .env are missing (ACC-003)."""

    def setUp(self):
        # Create an environment dictionary where all provider keys are stripped
        self.cleared_env = {key: "" for key in PROVIDER_KEYS.values()}

    async def test_app_starts_normally_with_missing_keys(self):
        """Verify app boots normally with 200 OK when all provider keys are absent (ACC-003)."""
        with patch.dict(os.environ, self.cleared_env, clear=False):
            # Lifespan context simulates application startup and shutdown
            async with lifespan(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8000",
            ) as client:
                # 1. Health check must be 200 OK
                health_res = await client.get("/health")
                self.assertEqual(health_res.status_code, 200)
                self.assertEqual(health_res.json().get("status"), "healthy")

                # 2. Config status endpoint must show "Not Configured" for all providers
                config_res = await client.get("/api/config/status")
                self.assertEqual(config_res.status_code, 200)

                data = config_res.json()
                providers = data.get("providers", {})

                for provider_name in ["gemini", "groq", "openai", "openrouter"]:
                    prov = providers.get(provider_name, {})
                    self.assertFalse(
                        prov.get("configured"),
                        f"Provider {provider_name} should be unconfigured",
                    )
                    self.assertEqual(
                        prov.get("status"),
                        "Not Configured",
                        f"Provider {provider_name} status must be 'Not Configured'",
                    )
                    self.assertIsNone(
                        prov.get("masked_key"),
                        f"Provider {provider_name} masked key must be None",
                    )

                # 3. Other features and endpoints remain operable
                root_res = await client.get("/")
                self.assertEqual(root_res.status_code, 200)
                self.assertEqual(root_res.json().get("status"), "online")

    async def test_partial_key_removal_operability(self):
        """Verify removing one key updates its status to 'Not Configured' while others stay operable."""
        mixed_env = {
            "GEMINI_API_KEY": "",  # Removed
            "OPENAI_API_KEY": "sk-activeTestKey1234567890abcdef",  # Present
        }
        with patch.dict(os.environ, mixed_env, clear=False):
            async with lifespan(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://127.0.0.1:8000",
            ) as client:
                config_res = await client.get("/api/config/status")
                self.assertEqual(config_res.status_code, 200)

                data = config_res.json()
                providers = data.get("providers", {})

                # Gemini is Not Configured
                gemini = providers.get("gemini", {})
                self.assertFalse(gemini.get("configured"))
                self.assertEqual(gemini.get("status"), "Not Configured")
                self.assertIsNone(gemini.get("masked_key"))

                # OpenAI is Configured
                openai = providers.get("openai", {})
                self.assertTrue(openai.get("configured"))
                self.assertEqual(openai.get("status"), "Configured")
                self.assertEqual(openai.get("masked_key"), "••••cdef")

    def test_app_config_direct_missing_behavior(self):
        """Direct unit assertion on AppConfig class without .env."""
        with patch.dict(os.environ, self.cleared_env, clear=False):
            cfg = AppConfig()
            self.assertFalse(cfg.is_provider_configured("gemini"))
            self.assertFalse(cfg.is_provider_configured("groq"))
            self.assertIsNone(cfg.get_raw_key("gemini"))

            status = cfg.get_provider_status("gemini")
            self.assertEqual(status["status"], "Not Configured")
            self.assertFalse(status["configured"])
            self.assertIsNone(status["masked_key"])


if __name__ == "__main__":
    unittest.main()
