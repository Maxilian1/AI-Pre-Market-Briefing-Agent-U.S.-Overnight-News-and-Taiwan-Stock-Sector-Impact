"""Input/output helpers for raw news metadata."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from src.news_collectors.base import NewsItem
from src.news_collectors.dedupe import (
    canonicalize_url,
    compute_payload_hash,
    hash_text,
    normalize_title,
)
from src.time_utils import normalize_to_utc


NEWS_FIELDNAMES = [
    "news_id",
    "source",
    "title",
    "url",
    "published_at_utc",
    "retrieved_at_utc",
    "raw_summary",
    "raw_payload_hash",
    "canonical_url",
    "normalized_title_hash",
    "collection_mode",
    "duplicate_group_id",
    "duplicate_key_type",
]


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _optional_utc_iso(value: str | None) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return normalize_to_utc(str(value)).isoformat()
    except (TypeError, ValueError):
        return None


def _news_item_from_record(record: dict, collection_mode: str = "fixture") -> NewsItem:
    title = str(record.get("title", "")).strip()
    source = str(record.get("source", "")).strip()
    url = record.get("url")
    raw_summary = record.get("raw_summary") or record.get("summary")
    published_at_utc = _optional_utc_iso(record.get("published_at_utc") or record.get("published_at"))
    retrieved_at_utc = _optional_utc_iso(record.get("retrieved_at_utc")) or _utc_iso_now()
    canonical_url = canonicalize_url(str(url)) if url else None
    normalized_title_hash = hash_text(normalize_title(title))
    payload = {
        "source": source,
        "title": title,
        "url": url,
        "published_at_utc": published_at_utc,
        "raw_summary": raw_summary,
    }
    raw_payload_hash = str(record.get("raw_payload_hash") or compute_payload_hash(payload))
    news_id = str(
        record.get("news_id")
        or hash_text(f"{source}|{canonical_url or ''}|{normalized_title_hash}|{published_at_utc or ''}")[:16]
    )

    return NewsItem(
        news_id=news_id,
        source=source,
        title=title,
        url=str(url) if url else None,
        published_at_utc=published_at_utc,
        retrieved_at_utc=retrieved_at_utc,
        raw_summary=str(raw_summary) if raw_summary else None,
        raw_payload_hash=raw_payload_hash,
        canonical_url=canonical_url,
        normalized_title_hash=normalized_title_hash,
        collection_mode=str(record.get("collection_mode") or collection_mode),
    )


def _row_dict(item: dict | NewsItem) -> dict:
    if isinstance(item, NewsItem):
        return item.to_dict()
    return dict(item)


def save_news_csv(items: list[dict] | list[NewsItem], output_path) -> Path:
    """Save news rows to CSV using a stable column order."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [_row_dict(item) for item in items]
    extra_fields = sorted({key for row in rows for key in row} - set(NEWS_FIELDNAMES))
    fieldnames = NEWS_FIELDNAMES + extra_fields

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return path


def load_news_csv(input_path) -> list[dict]:
    """Load saved raw news CSV rows."""

    path = Path(input_path)
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def load_fixture_news(path) -> list[NewsItem]:
    """Load synthetic fixture records and convert them to NewsItem objects."""

    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as json_file:
        payload = json.load(json_file)

    if not isinstance(payload, list):
        raise ValueError("Fixture news file must contain a JSON list of records.")

    return [_news_item_from_record(record, collection_mode="fixture") for record in payload]
