# Local Install, Run, Update and Recovery Guide — Intended Behavior

This document defines the exact operational instructions and commands for running ILLUM AI Studio locally (governed by ADR-001 and Python 3.12).

## First install (Windows & POSIX Local Mode)

### Windows 10/11:
1. Install Python 3.12 (64-bit) from python.org (ensure "Add Python to PATH" is checked).
2. Clone repository:
   ```cmd
   git clone <repo-url>
   cd illum-ai-studio
   ```
3. Run the automated desktop launcher:
   ```cmd
   run.bat
   ```
   *Alternatively, manual setup in PowerShell or cmd:*
   ```cmd
   python -m venv venv
   call venv\Scripts\activate.bat
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   copy .env.example .env
   ```
4. Open `.env` in Notepad and insert your API keys (e.g. `GEMINI_API_KEY`).
5. Launch the application:
   ```cmd
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
6. Open your web browser at `http://127.0.0.1:8000`.

### Linux / macOS:
1. Ensure Python 3.12 (or 3.11 fallback) is installed.
2. Run launcher:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   *Or manual setup:*
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

## Normal use

- Start app using documented launcher.
- Select/create project, set ratio/duration/language/provider/model.
- Add and validate source directly, or optionally use Idea Research if implemented.
- Generate script and approve exact current version before downstream skills.
- Export project before risky updates/deletion.

### API Key Configuration & Restart Workflow (DEC-003, P02-T03)

1. **Adding or Updating Keys:**
   - Open `.env` in Notepad (copied from `.env.example`).
   - Enter your provider API keys (e.g., `GEMINI_API_KEY=AIzaSy...`, `GROQ_API_KEY=gsk_...`).
   - Save the file as standard UTF-8 text in Notepad.
   - **Explicit Server Restart Required:** Changes made to `.env` take effect on the next application launch. Restart `run.bat` (Windows) or `run.sh` (Linux/macOS) to activate the updated configuration.
2. **Removing or Clearing Keys:**
   - Delete the key line from `.env` or set it to empty (`GEMINI_API_KEY=`).
   - Save and restart the server.
   - The provider immediately returns to "Not Configured" state. The application continues running normally without crashing (ACC-003).
   - *Note:* Removing a key locally disables the local provider connection; it does **not** revoke the key on the provider's remote servers.
3. **Environment Isolation & Precedence:**
   - The application strictly tracks keys loaded from local `.env`.
   - Modifying or clearing `.env` keys never alters or clears unrelated external system environment variables.
   - Precedence: Explicit parameters/injected values > External system environment variables > Local `.env` values > Default fallback settings.

## Updating from GitHub

1. Export/backup important project data first.
2. Stop application and jobs.
3. Review release notes and migration notes.
4. Fetch/pull only the approved release/branch; avoid overwriting local `.env`.
5. Install updated pinned dependencies.
6. Run migrations and tests as documented.
7. Start app and check provider connection/project integrity.
8. Roll back application code if necessary; database rollback policy must be explicit before release.

## Verifying Clean-Install Smoke Procedure

From a clean checkout or newly configured environment, execute the automated smoke procedure:
```bash
python3 scripts/smoke_clean_install.py
```
This verifies:
1. Python version compatibility (Python 3.12 target per ADR-001; 3.11+ supported).
2. All pinned core dependencies import cleanly without missing modules.
3. `.env.example` contains only sanitized placeholders (no real secrets).
4. Desktop launcher scripts (`run.bat` and `run.sh`) enforce strict `127.0.0.1:8000` loopback binding.
5. `.gitignore` excludes `.env`, `data/`, `logs/`, and `tmp/`.
6. Application starts, responds to `/health` (HTTP 200), `/`, and `/api/config/status` (masked keys verified), and shuts down cleanly.
7. Absence of undocumented local developer paths or hidden prerequisites.

## Troubleshooting expectations

Errors should state actionable guidance without exposing secrets:
- **Missing `ensurepip` (Debian/Ubuntu):** Install `python3-venv` via `sudo apt install python3-venv`, or create venv with `python3 -m venv --without-pip --system-site-packages venv`.
- **Missing `python` on PATH (Windows):** Re-run Python 3.12 installer and ensure the "Add Python to PATH" checkbox is selected.
- **Port Conflict (Port 8000 in use):** Terminate conflicting local process or set `PORT=8001` in `.env`.
- **Missing or Unconfigured API Keys:** Normal operation per ACC-003; AI providers report "Not Configured" while project creation, editing, and health endpoints remain 100% operational.
- **Secret Redaction:** Logs never record raw API keys or provider payloads.

## Backup/restore boundary

Export is data-only and the approved app plan does not approve in-app restore. Users may preserve exported ZIPs externally. Do not present export as a guaranteed import/restore backup.
