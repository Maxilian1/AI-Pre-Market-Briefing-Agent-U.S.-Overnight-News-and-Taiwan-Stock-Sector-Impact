"""Deterministic deduplication helpers for raw news metadata."""

from __future__ import annotations

import hashlib
import json
import re
import string
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.news_collectors.base import NewsItem


TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_name",
    "utm_reader",
    "utm_viz_id",
    "utm_pubreferrer",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(url: str | None) -> str | None:
    """Return a deterministic URL with common tracking parameters removed."""

    if url is None:
        return None

    stripped = url.strip()
    if not stripped:
        return None

    parsed = urlsplit(stripped)
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    ]
    query = urlencode(sorted(filtered_query), doseq=True)
    path = parsed.path.rstrip("/") or parsed.path

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            query,
            "",
        )
    )


def normalize_title(title: str) -> str:
    """Lowercase, remove simple punctuation, and collapse whitespace."""

    punctuation_table = str.maketrans({char: " " for char in string.punctuation})
    no_punctuation = title.lower().strip().translate(punctuation_table)
    return re.sub(r"\s+", " ", no_punctuation).strip()


def hash_text(value: str) -> str:
    """Return a SHA-256 hash for deterministic IDs and grouping."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_payload_hash(payload: dict) -> str:
    """Hash a JSON-serializable payload deterministically."""

    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hash_text(encoded)


def assign_duplicate_group_ids(items: list[NewsItem]) -> list[dict]:
    """Attach duplicate group IDs, preferring canonical URL over title hash.

    No fuzzy matching is used in Phase 2. Items with a canonical URL group by
    that URL. Items without a URL group by their normalized title hash.
    """

    rows = []
    for item in items:
        row = item.to_dict()
        if item.canonical_url:
            duplicate_key = f"url:{item.canonical_url}"
        else:
            duplicate_key = f"title:{item.normalized_title_hash}"

        row["duplicate_group_id"] = hash_text(duplicate_key)[:16]
        row["duplicate_key_type"] = duplicate_key.split(":", maxsplit=1)[0]
        rows.append(row)

    return rows
