"""Shared CLI validation helpers."""

from __future__ import annotations

from datetime import date


PLACEHOLDER_DATES = {
    "yyyy-mm-dd",
    "yyyymmdd",
    "date",
    "today",
    "null",
    "none",
}


def validate_iso_date(date_value: str) -> str:
    """Validate a CLI date and return normalized ISO format."""

    value = str(date_value).strip()
    if not value or value.lower() in PLACEHOLDER_DATES:
        raise ValueError(f"Invalid date value: {date_value!r}")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date value: {date_value!r}") from exc
