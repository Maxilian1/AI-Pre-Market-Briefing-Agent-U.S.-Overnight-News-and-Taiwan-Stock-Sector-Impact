"""Markdown report I/O helpers."""

from __future__ import annotations

from pathlib import Path


def save_markdown_report(markdown_text: str, output_path) -> Path:
    """Save a Markdown report to disk."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown_text, encoding="utf-8")
    return path


def load_markdown_report(path) -> str:
    """Load a Markdown report from disk."""

    return Path(path).read_text(encoding="utf-8")
