import sys
import types
from unittest.mock import patch

from src.news_collectors.rss_collector import collect_from_feed


def test_rss_collector_uses_feed_metadata_without_article_body_fetch():
    fake_entry = {
        "title": "Nvidia AI metadata headline",
        "link": "https://example.com/article?utm_source=test",
        "summary": "RSS-provided snippet only.",
        "content": [{"value": "Synthetic full content that must not be stored."}],
        "published": "Thu, 15 Jan 2026 00:00:00 GMT",
    }
    fake_feedparser = types.SimpleNamespace(
        parse=lambda feed_url: types.SimpleNamespace(entries=[fake_entry])
    )

    with patch.dict(sys.modules, {"feedparser": fake_feedparser}):
        items = collect_from_feed("https://example.com/feed.xml", "Fake RSS")

    assert len(items) == 1
    item = items[0]
    row = item.to_dict()

    assert item.collection_mode == "rss"
    assert item.raw_summary == "RSS-provided snippet only."
    assert item.canonical_url == "https://example.com/article"
    assert item.published_at_utc.endswith("+00:00")
    assert item.retrieved_at_utc.endswith("+00:00")
    assert "content" not in row
    assert "article_body" not in row
