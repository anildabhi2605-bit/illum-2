"""Acceptance test: Clean-install smoke procedure verification (P01-T05)."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.smoke_clean_install import (
    check_env_example_safety,
    check_gitignore_boundary,
    check_launcher_scripts,
    check_no_developer_hidden_steps,
    check_pinned_dependencies,
    check_python_version,
    check_runtime_endpoints,
    is_supported_python_version,
)


class TestCleanInstallSmoke:
    """End-to-end verification of clean checkout and local execution procedure."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_python_compatibility_specification_and_bounds(self):
        """Verify Python constraint is strictly >=3.11, <3.13 and Python 3.10 is NOT supported."""
        # 3.10 must NOT be supported
        assert is_supported_python_version((3, 10)) is False
        # 3.11 and 3.12 must be supported
        assert is_supported_python_version((3, 11)) is True
        assert is_supported_python_version((3, 12)) is True
        # >=3.13 must NOT be supported
        assert is_supported_python_version((3, 13)) is False
        assert is_supported_python_version((3, 9)) is False

        # pyproject.toml must enforce this constraint
        pyproject = self.ROOT / "pyproject.toml"
        assert pyproject.exists()
        assert 'requires-python = ">=3.11, <3.13"' in pyproject.read_text(encoding="utf-8")

        # Smoke check procedure executes with container warning without claiming 3.10 support
        assert check_python_version() is True


    def test_pinned_dependencies_import(self):
        """Verify all pinned dependencies from requirements.txt can be imported."""
        assert check_pinned_dependencies() is True

    def test_env_example_contains_only_placeholders(self):
        """Verify .env.example contains no real secrets or production keys."""
        assert check_env_example_safety() is True

    def test_launcher_scripts_strict_localhost(self):
        """Verify run.bat and run.sh enforce 127.0.0.1:8000 loopback binding."""
        assert check_launcher_scripts() is True

    def test_gitignore_protects_secrets_and_runtime_dirs(self):
        """Verify .gitignore excludes .env, data/, logs/, and tmp/."""
        assert check_gitignore_boundary() is True

    @pytest.mark.asyncio
    async def test_runtime_endpoints_and_lifecycle(self):
        """Verify application starts, returns health/status, masks keys, and shuts down cleanly."""
        result = await check_runtime_endpoints()
        assert result is True

    def test_no_undocumented_hidden_developer_paths(self):
        """Verify codebase does not contain machine-specific absolute developer paths."""
        assert check_no_developer_hidden_steps() is True
