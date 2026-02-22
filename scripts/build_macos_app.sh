#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv-build}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "error: python binary not found: $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null
python -m pip install .[build] >/dev/null

python -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "Clipboard Cleaner" \
  --paths src \
  --hidden-import tkinter \
  src/clipboard_cleaner/__main__.py

echo "Built: $ROOT_DIR/dist/Clipboard Cleaner.app"
