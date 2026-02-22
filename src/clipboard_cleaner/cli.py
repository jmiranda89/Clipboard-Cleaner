"""Command-line entrypoint for clipboard cleaner."""

from __future__ import annotations

import argparse
import sys

from .app import run_gui
from .cleaning import clean_text


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clipboard-cleaner",
        description="Clean clipboard text while preserving line breaks and indentation.",
    )
    parser.add_argument(
        "--clean-stdin",
        action="store_true",
        help="Read stdin, clean text, and print to stdout.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Start GUI with auto-clean mode enabled.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.clean_stdin:
        text = sys.stdin.read()
        sys.stdout.write(clean_text(text))
        return 0

    run_gui(auto_mode=args.auto)
    return 0
