"""Unit tests: Dependency consistency and pinning validation (P01-T02)."""
import re
import unittest
from pathlib import Path
from typing import ClassVar


class TestDependencyConsistency(unittest.TestCase):
    """Assert all dependencies in requirements.txt and pyproject.toml are pinned and conform to ADR-001."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    # Approved core packages from ADR-001
    APPROVED_CORE: ClassVar[set[str]] = {
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic-settings",
        "sqlalchemy",
        "alembic",
        "python-dotenv",
        "httpx",
        "jinja2",
    }

    # Prohibited until governing phase / tests pass (DEC-007 is OPEN; Module E is P14)
    PROHIBITED_UNVERIFIED: ClassVar[set[str]] = {
        "google-generativeai",
        "google-genai",
        "openai",
        "anthropic",
        "groq",
        "praw",
        "tweepy",
        "selenium",
        "playwright",
        "beautifulsoup4",
    }

    def test_requirements_file_exists_and_pinned(self):
        req_path = self.ROOT / "requirements.txt"
        self.assertTrue(req_path.exists(), "requirements.txt must exist at root")

        lines = req_path.read_text(encoding="utf-8").splitlines()
        dep_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

        self.assertGreater(len(dep_lines), 0, "requirements.txt must declare dependencies")

        for line in dep_lines:
            base_pkg = re.split(r"[=<>]", line)[0].strip()
            # Handle extras like uvicorn[standard]
            clean_pkg = re.sub(r"\[.*\]", "", base_pkg).strip()

            self.assertIn(
                "==",
                line,
                f"Dependency '{line}' must be strictly pinned with '==' per P01-T02",
            )
            self.assertIn(
                clean_pkg,
                self.APPROVED_CORE,
                f"Package '{clean_pkg}' is not in approved ADR-001 core stack",
            )
            self.assertNotIn(
                clean_pkg,
                self.PROHIBITED_UNVERIFIED,
                f"Package '{clean_pkg}' is prohibited before explicit provider approval (DEC-007)",
            )

    def test_pyproject_toml_matches_requirements(self):
        pyproj_path = self.ROOT / "pyproject.toml"
        self.assertTrue(pyproj_path.exists(), "pyproject.toml must exist at root")
        content = pyproj_path.read_text(encoding="utf-8")

        # Check Python version constraint
        self.assertIn(
            'requires-python = ">=3.11, <3.13"',
            content,
            "pyproject.toml must declare '>=3.11, <3.13' per ADR-001 Python 3.12 target",
        )

        for pkg in self.APPROVED_CORE:
            self.assertIn(
                pkg,
                content,
                f"Core package '{pkg}' must be referenced in pyproject.toml",
            )

    def test_launcher_scripts_bind_localhost(self):
        run_bat = self.ROOT / "run.bat"
        run_sh = self.ROOT / "run.sh"

        self.assertTrue(run_bat.exists(), "run.bat must exist")
        self.assertTrue(run_sh.exists(), "run.sh must exist")

        bat_text = run_bat.read_text(encoding="utf-8")
        sh_text = run_sh.read_text(encoding="utf-8")

        self.assertIn("127.0.0.1", bat_text, "run.bat must bind strictly to 127.0.0.1")
        self.assertIn("127.0.0.1", sh_text, "run.sh must bind strictly to 127.0.0.1")
        self.assertIn("requirements.txt", bat_text)
        self.assertIn("requirements.txt", sh_text)


if __name__ == "__main__":
    unittest.main()
