# Clipboard Cleaner

A lightweight clipboard cleaner that keeps only plain text while preserving line breaks and indentation.

## Features

- Desktop GUI built with Tkinter
- Optional auto-clean mode that watches new clipboard text
- CLI mode for text pipelines (`stdin -> stdout`)
- macOS `.app` bundle build with PyInstaller

## Install and run (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
clipboard-cleaner
```

Or run directly from source:

```bash
PYTHONPATH=src python -m clipboard_cleaner
```

## CLI usage

```bash
echo $'A\r\nB\u00A0C' | clipboard-cleaner --clean-stdin
```

## Build macOS app bundle

```bash
./scripts/build_macos_app.sh
```

The output app bundle will be written to `dist/Clipboard Cleaner.app`.

## Development

```bash
pip install -e .[dev]
pytest
```
