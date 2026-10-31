# ILLUM AI STUDIO

Desktop workbench for YouTube Script, Video Prompts, Thumbnail & SEO Studio production.

Start with [`00_START_HERE/INDEX.md`](00_START_HERE/INDEX.md), then read [`00_START_HERE/README_START_HERE.md`](00_START_HERE/README_START_HERE.md).

---

## Quickstart & Local Installation (ADR-001)

ILLUM AI STUDIO runs locally on **Python 3.12** (Python 3.11+ supported). Per approved **ADR-001**, the user runtime requires **ZERO Node.js or npm dependencies**. The local server binds strictly to loopback `http://127.0.0.1:8000`.

### 1. Windows 10/11 (Primary Target)
1. Install **Python 3.12 (64-bit)** from [python.org](https://www.python.org/) (ensure **"Add Python to PATH"** is checked).
2. Clone repository:
   ```cmd
   git clone <repo-url>
   cd illum-ai-studio
   ```
3. Run the automated desktop launcher:
   ```cmd
   run.bat
   ```
   *The launcher automatically initializes `venv\`, installs pinned dependencies from `requirements.txt`, creates `.env` from `.env.example`, and launches the studio on `http://127.0.0.1:8000`.*
4. Open `.env` in Notepad to enter your AI provider API key (e.g. `GEMINI_API_KEY`).

### 2. Linux / macOS
1. Ensure Python 3.11+ is installed.
2. Run the automated desktop launcher:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
3. Open `.env` in your text editor and configure your provider keys.

### 3. Manual Setup (Terminal / PowerShell)
```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env        # On Windows: copy .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Verifying Setup & Running Tests

- **Run Clean-Install Smoke Procedure:**
  ```bash
  python3 scripts/smoke_clean_install.py
  ```
- **Run Full Automated Test Suite (Pytest):**
  ```bash
  python3 -m pytest -v
  ```
- **Run Linting & Code Hygiene (Ruff):**
  ```bash
  python3 -m ruff check .
  ```

---

## Common Failures & Troubleshooting

1. **`ensurepip is not available` on Debian/Ubuntu:**
   - Cause: Minimal system Python packages omit the standard `ensurepip` module.
   - Solution: Run `sudo apt install python3-venv` (or use `python3 -m venv --without-pip --system-site-packages venv`).
2. **`Port 8000 is already in use`:**
   - Cause: Another process is listening on port 8000.
   - Solution: Terminate the existing process or set `PORT=8001` in `.env`. The launcher will bind `127.0.0.1:<PORT>`.
3. **`GEMINI_API_KEY not configured`:**
   - Cause: `.env` has not been configured with your API key.
   - Solution: Normal graceful degradation per ACC-003. Non-AI features, project management, and health routes remain 100% operational. Copy your key into `.env`.
4. **Secrets / API Keys Security:**
   - Never commit `.env` to Git. The repository `.gitignore` strictly ignores `.env`, `data/`, `logs/`, and `tmp/`.
   - Keys are masked in the UI (`••••cdef`) and automatically redacted from application logs.

---

## Documentation & Phase Tracking
- 16 ordered build phases (`P00`–`P15`)
- Phase and task index: [`04_BUILD_TASKS/PHASE_INDEX.md`](04_BUILD_TASKS/PHASE_INDEX.md)
- Implementation status board: [`07_CHANGE_CONTROL/IMPLEMENTATION_STATUS.md`](07_CHANGE_CONTROL/IMPLEMENTATION_STATUS.md)
- Change log: [`07_CHANGE_CONTROL/CHANGELOG.md`](07_CHANGE_CONTROL/CHANGELOG.md)
