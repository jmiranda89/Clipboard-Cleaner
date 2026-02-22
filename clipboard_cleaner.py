"""Compatibility launcher for running from source checkout."""

from __future__ import annotations

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from clipboard_cleaner.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
