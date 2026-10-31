"""Integration tests: Local runtime entrypoint, health endpoint, and lifecycle (P01-T03)."""
import os
import unittest
from pathlib import Path

import httpx

from app import __version__
from app.main import DEFAULT_HOST, DEFAULT_PORT, app, lifespan


class TestServerLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying server startup, health endpoint, host binding, and sanitized error handling."""

    async def test_health_check_endpoint(self):
        """Verify GET /health returns 200 and healthy metadata."""
        expected_port = int(os.getenv("PORT", str(DEFAULT_PORT)))
        async with lifespan(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=f"http://{DEFAULT_HOST}:{expected_port}",
        ) as client:
            response = await client.get("/health")
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(data.get("status"), "healthy")
            self.assertEqual(data.get("app"), "ILLUM AI STUDIO")
            self.assertEqual(data.get("version"), __version__)
            self.assertEqual(data.get("host"), DEFAULT_HOST)
            self.assertEqual(data.get("port"), expected_port)

    async def test_root_status_endpoint(self):
        """Verify GET / returns 200 and online status."""
        expected_port = int(os.getenv("PORT", str(DEFAULT_PORT)))
        async with lifespan(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=f"http://{DEFAULT_HOST}:{expected_port}",
        ) as client:
            response = await client.get("/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data.get("status"), "online")
            self.assertEqual(data.get("app"), "ILLUM AI STUDIO")

    async def test_not_found_handling(self):
        """Verify 404 on unmapped endpoint."""
        expected_port = int(os.getenv("PORT", str(DEFAULT_PORT)))
        async with lifespan(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=f"http://{DEFAULT_HOST}:{expected_port}",
        ) as client:
            response = await client.get("/non_existent_route_xyz")
            self.assertEqual(response.status_code, 404)

    async def test_sanitized_500_exception_handler(self):
        """Verify unhandled exceptions return sanitized 500 without leaking stack traces or keys."""
        # Temporarily register a fault injection route
        @app.get("/test-fault-injection")
        async def fault_injection():
            raise RuntimeError("Simulated internal crash with secret_key=test_sentinel_xyz123")

        try:
            expected_port = int(os.getenv("PORT", str(DEFAULT_PORT)))
            async with lifespan(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                base_url=f"http://{DEFAULT_HOST}:{expected_port}",
            ) as client:
                response = await client.get("/test-fault-injection")
                self.assertEqual(response.status_code, 500)
                data = response.json()
                self.assertEqual(data.get("error"), "InternalServerError")
                self.assertNotIn("test_sentinel_xyz123", str(data))
                self.assertNotIn("Traceback", str(data))
        finally:
            # Clean up route
            app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-fault-injection"]

    def test_localhost_binding_defaults(self):
        """Verify default binding constants enforce 127.0.0.1 loopback."""
        self.assertEqual(DEFAULT_HOST, "127.0.0.1")
        self.assertEqual(DEFAULT_PORT, 8000)

    async def test_lifespan_creates_runtime_directories(self):
        """Verify lifespan startup creates data, logs, tmp, exports runtime directories."""
        async with lifespan(app):
            self.assertTrue(Path("data").is_dir())
            self.assertTrue(Path("logs").is_dir())
            self.assertTrue(Path("tmp").is_dir())
            self.assertTrue(Path("exports").is_dir())
            self.assertTrue(getattr(app.state, "healthy", False))

        self.assertFalse(getattr(app.state, "healthy", True))


if __name__ == "__main__":
    unittest.main()
