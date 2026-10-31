"""Repository secret hygiene scanner (P02-T02, ACC-002, DEC-003).

Features:
- Verifies .gitignore rules exclude .env, .env.*, data/, logs/, tmp/, exports/.
- Scans .env.example to ensure only sanitized placeholders exist.
- Scans repository source files to ensure no real API keys or tokens are committed.
- Can be executed directly or imported in test suites.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Sensitive file patterns that must never be tracked or committed
SENSITIVE_PATTERNS = [
    re.compile(r"^\.env$", re.IGNORECASE),
    re.compile(r"^\.env\.(local|dev|production|prod|secret)$", re.IGNORECASE),
    re.compile(r".*\.(pem|key|p12|pfx)$", re.IGNORECASE),
    re.compile(r"^id_rsa.*", re.IGNORECASE),
]

# Patterns representing plausible real API keys
SECRET_REGEXES = [
    (re.compile(r"(?:gsk_[a-zA-Z0-9]{20,})"), "Groq API Key"),
    (re.compile(r"(?:sk-[a-zA-Z0-9]{20,})"), "OpenAI/OpenRouter API Key"),
    (re.compile(r"(?:AIzaSy[a-zA-Z0-9_-]{33})"), "Google API Key"),
]

# Excluded paths for content scanning
IGNORE_DIRS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "venv",
    ".venv",
    "node_modules",
    "data",
    "logs",
    "tmp",
    "exports",
}


def check_gitignore_rules(root: Path = ROOT_DIR) -> tuple[bool, list[str]]:
    """Verify that .gitignore contains all required secret and local data exclusions."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return False, [".gitignore file does not exist at project root."]

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    required_patterns = [".env", ".env.*", "data/", "logs/", "tmp/", "exports/"]
    missing = [pat for pat in required_patterns if pat not in lines]

    if missing:
        return False, [f"Missing required .gitignore rule: {pat}" for pat in missing]

    return True, []


def check_env_example_cleanliness(root: Path = ROOT_DIR) -> tuple[bool, list[str]]:
    """Verify that .env.example contains only safe placeholders and no real secrets."""
    example_path = root / ".env.example"
    if not example_path.exists():
        return False, [".env.example file does not exist at project root."]

    content = example_path.read_text(encoding="utf-8")
    errors = []

    for idx, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")

            if any(term in key.upper() for term in ["KEY", "SECRET", "TOKEN", "PASSWORD"]):
                if val and not any(allowed in val.lower() for allowed in ["your_", "placeholder", "dummy", "example"]):
                    errors.append(f"Line {idx}: Key '{key}' has non-placeholder value.")

    return len(errors) == 0, errors


def scan_for_untracked_secrets(root: Path = ROOT_DIR) -> tuple[bool, list[str]]:
    """Scan source files for accidentally hardcoded API key patterns."""
    errors = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            rel_file = Path(dirpath, filename).relative_to(root)

            # Check if sensitive file name
            for pat in SENSITIVE_PATTERNS:
                if pat.match(filename):
                    errors.append(f"Sensitive file located in workspace: {rel_file}")

            # Check source file content (skip binary, image, or doc archives)
            if filename.endswith((".py", ".json", ".md", ".sh", ".bat", ".toml", ".txt")):
                file_path = Path(dirpath, filename)
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Skip checking test files that deliberately use mock/sentinel test fixtures
                if filename.startswith("test_") or "test" in filename.lower() or "check_secret_hygiene.py" in filename:
                    continue

                for regex, desc in SECRET_REGEXES:
                    match = regex.search(text)
                    if match:
                        matched_str = match.group(0)
                        # Filter out known safe placeholders
                        if not any(safe in matched_str.lower() for safe in ["example", "placeholder", "test", "dummy"]):
                            errors.append(
                                f"Possible live secret ({desc}) detected in {rel_file}: {matched_str[:6]}..."
                            )

    return len(errors) == 0, errors


def main() -> int:
    """Run full repository secret hygiene checks."""
    print("==================================================")
    print("   ILLUM AI STUDIO — Secret Hygiene Scanner")
    print("==================================================")

    all_passed = True

    # 1. Check .gitignore
    ok_git, git_errs = check_gitignore_rules()
    if ok_git:
        print("[PASS] .gitignore rules verified (secrets and runtime directories excluded).")
    else:
        print("[FAIL] .gitignore check failed:")
        for err in git_errs:
            print(f"       - {err}")
        all_passed = False

    # 2. Check .env.example
    ok_ex, ex_errs = check_env_example_cleanliness()
    if ok_ex:
        print("[PASS] .env.example verified (only sanitized placeholders present).")
    else:
        print("[FAIL] .env.example check failed:")
        for err in ex_errs:
            print(f"       - {err}")
        all_passed = False

    # 3. Check for hardcoded secrets
    ok_scan, scan_errs = scan_for_untracked_secrets()
    if ok_scan:
        print("[PASS] Repository source files clean (zero exposed live secrets).")
    else:
        print("[FAIL] Secret scanning detected potential issues:")
        for err in scan_errs:
            print(f"       - {err}")
        all_passed = False

    print("==================================================")
    if all_passed:
        print("RESULT: ALL SECRET HYGIENE CHECKS PASSED.")
        return 0
    else:
        print("RESULT: SECRET HYGIENE CHECKS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
