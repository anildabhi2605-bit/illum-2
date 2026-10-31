"""Unit test: Verify package skeleton imports and module boundaries (P01-T01)."""
import importlib
import unittest
from typing import ClassVar


class TestSkeletonImports(unittest.TestCase):
    """Smoke test asserting all skeleton modules import cleanly without circular dependencies."""

    MODULES: ClassVar[list[str]] = [
        "app",
        "app.main",
        "app.domain",
        "app.persistence",
        "app.providers",
        "app.jobs",
        "app.skills",
        "app.research",
        "app.security",
        "app.use_cases",
        "app.ui",
        "migrations",
        "tests",
        "tests.unit",
        "tests.integration",
        "tests.acceptance",
        "tests.security",
    ]

    def test_all_modules_import_cleanly(self):
        for mod_name in self.MODULES:
            with self.subTest(module=mod_name):
                mod = importlib.import_module(mod_name)
                self.assertIsNotNone(mod, f"Module {mod_name} failed to import")

    def test_app_version_defined(self):
        import app
        self.assertTrue(hasattr(app, "__version__"))
        self.assertIsInstance(app.__version__, str)


if __name__ == "__main__":
    unittest.main()
