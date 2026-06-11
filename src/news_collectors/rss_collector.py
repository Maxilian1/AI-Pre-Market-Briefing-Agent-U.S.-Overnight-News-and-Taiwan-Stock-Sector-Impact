"""Public RSS metadata collector.

The collector stores feed-provided metadata only. It does not fetch article
pages, scrape full article bodies, or bypass paywalls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from src.news_collectors.base import NewsItem
from src.news_collectors.dedupe import (
    canonicalize_url,
    compute_payload_hash,
    hash_text,
    normalize_title,
)
from src.time_utils import normalize_to_utc


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _published_to_utc_iso(entry: dict) -> str | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_time:
        try:
            timestamp = datetime(*parsed_time[:6], tzinfo=timezone.utc)
            return normalize_to_utc(timestamp).isoformat()
        except (TypeError, ValueError):
            return None

    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            return normalize_to_utc(parsedate_to_datetime(value)).isoformat()
        except (TypeError, ValueError, IndexError, OverflowError):
            continue

    return None


def _entry_to_news_item(entry: dict, source_name: str, retrieved_at_utc: str) -> NewsItem:
    title = str(entry.get("title", "")).strip()
    url = entry.get("link")
    raw_summary = entry.get("summary") or entry.get("description")
    published_at_utc = _published_to_utc_iso(entry)
    canonical_url = canonicalize_url(str(url)) if url else None
    normalized_title_hash = hash_text(normalize_title(title))
    payload = {
        "source": source_name,
        "title": title,
        "url": url,
        "published_at_utc": published_at_utc,
        "raw_summary": raw_summary,
    }
    raw_payload_hash = compute_payload_hash(payload)
    news_id = hash_text(f"{source_name}|{canonical_url or ''}|{normalized_title_hash}|{published_at_utc or ''}")[:16]

    return NewsItem(
        news_id=news_id,
        source=source_name,
        title=title,
        url=str(url) if url else None,
        published_at_utc=published_at_utc,
        retrieved_at_utc=retrieved_at_utc,
        raw_summary=str(raw_summary) if raw_summary else None,
        raw_payload_hash=raw_payload_hash,
        canonical_url=canonical_url,
        normalized_title_hash=normalized_title_hash,
        collection_mode="rss",
    )


def collect_from_feed(feed_url: str, source_name: str) -> list[NewsItem]:
    """Collect metadata records from one RSS/Atom feed."""

    import feedparser

    feed = feedparser.parse(feed_url)
    retrieved_at_utc = _utc_now_iso()
    return [_entry_to_news_item(entry, source_name, retrieved_at_utc) for entry in feed.entries]


def collect_from_feeds(feeds: list[dict]) -> list[NewsItem]:
    """Collect metadata records from feed configs with ``source`` and ``url``."""

    items = []
    for feed_config in feeds:
        source_name = feed_config["source"]
        feed_url = feed_config["url"]
        items.extend(collect_from_feed(feed_url=feed_url, source_name=source_name))
    return items
