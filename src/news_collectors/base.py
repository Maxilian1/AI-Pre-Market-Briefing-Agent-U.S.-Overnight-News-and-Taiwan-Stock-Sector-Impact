"""Raw news metadata schema for collection-stage records."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NewsItem:
    """Metadata-only news item.

    This schema intentionally stores RSS/API-provided metadata and snippets
    only. It is not a container for scraped article bodies.
    """

    news_id: str
    source: str
    title: str
    url: str | None
    published_at_utc: str | None
    retrieved_at_utc: str
    raw_summary: str | None
    raw_payload_hash: str
    canonical_url: str | None
    normalized_title_hash: str
    collection_mode: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
