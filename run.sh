#!/usr/bin/env bash
# ILLUM AI STUDIO — POSIX Desktop Launcher
set -euo pipefail

echo "========================================================"
echo "   ILLUM AI STUDIO — Local Desktop Launcher"
echo "========================================================"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "[INFO] Creating virtual environment in ./venv..."
    python3 -m venv venv
    # shellcheck disable=SC1091
    source venv/bin/activate
    echo "[INFO] Installing pinned dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[INFO] Initializing .env from .env.example..."
    cp .env.example .env
fi

echo "[INFO] Starting ILLUM AI STUDIO backend on http://127.0.0.1:8000 ..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
