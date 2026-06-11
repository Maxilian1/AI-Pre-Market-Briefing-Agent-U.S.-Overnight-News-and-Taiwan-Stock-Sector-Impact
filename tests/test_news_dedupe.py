from src.news_collectors.base import NewsItem
from src.news_collectors.dedupe import (
    assign_duplicate_group_ids,
    canonicalize_url,
    hash_text,
    normalize_title,
)


def _item(
    title: str,
    url: str | None,
    normalized_title_hash: str | None = None,
) -> NewsItem:
    return NewsItem(
        news_id=hash_text(f"{title}|{url or ''}")[:16],
        source="Test Source",
        title=title,
        url=url,
        published_at_utc="2026-01-15T00:00:00+00:00",
        retrieved_at_utc="2026-01-15T00:05:00+00:00",
        raw_summary="Synthetic test summary.",
        raw_payload_hash=hash_text(title),
        canonical_url=canonicalize_url(url),
        normalized_title_hash=normalized_title_hash or hash_text(normalize_title(title)),
        collection_mode="fixture",
    )


def test_url_canonicalization_removes_utm_parameters():
    url = "https://Example.com/news/story?b=2&utm_source=x&utm_medium=y&a=1#section"

    canonical = canonicalize_url(url)

    assert canonical == "https://example.com/news/story?a=1&b=2"


def test_title_normalization_lowercases_punctuation_and_spaces():
    title = "  NVIDIA:   AI Server Demand, Rises!  "

    assert normalize_title(title) == "nvidia ai server demand rises"


def test_duplicate_grouping_catches_same_canonical_url():
    first = _item("Nvidia AI server demand rises", "https://example.com/story?utm_source=a&id=1")
    second = _item("Different syndicated title", "https://example.com/story?id=1&utm_campaign=b")

    rows = assign_duplicate_group_ids([first, second])

    assert rows[0]["duplicate_group_id"] == rows[1]["duplicate_group_id"]
    assert rows[0]["duplicate_key_type"] == "url"


def test_duplicate_grouping_catches_same_normalized_title_when_url_missing():
    first = _item("AMD unveils AI accelerator roadmap!", None)
    second = _item("amd unveils ai accelerator roadmap", None)

    rows = assign_duplicate_group_ids([first, second])

    assert rows[0]["duplicate_group_id"] == rows[1]["duplicate_group_id"]
    assert rows[0]["duplicate_key_type"] == "title"
