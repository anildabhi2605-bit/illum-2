"""Security acceptance test: Secret hygiene and repository boundary check (P02-T02, ACC-002, DEC-003)."""
from __future__ import annotations

from pathlib import Path

from scripts.check_secret_hygiene import (
    check_env_example_cleanliness,
    check_gitignore_rules,
    scan_for_untracked_secrets,
)


class TestSecretHygieneAndBoundaries:
    """Verify repository .gitignore, .env.example, and absence of committed secrets."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_gitignore_contains_all_required_security_exclusions(self):
        """Verify .gitignore excludes .env, .env.*, data/, logs/, tmp/, and exports/."""
        passed, errors = check_gitignore_rules(self.ROOT)
        assert passed is True, f"Gitignore validation failed: {errors}"

    def test_env_example_has_only_safe_placeholders(self):
        """Verify .env.example contains zero real credentials or production keys."""
        passed, errors = check_env_example_cleanliness(self.ROOT)
        assert passed is True, f".env.example validation failed: {errors}"

    def test_repository_files_clean_of_live_secrets(self):
        """Scan source files to ensure no real API keys are present in repository."""
        passed, errors = scan_for_untracked_secrets(self.ROOT)
        assert passed is True, f"Found sensitive files or potential credentials: {errors}"
