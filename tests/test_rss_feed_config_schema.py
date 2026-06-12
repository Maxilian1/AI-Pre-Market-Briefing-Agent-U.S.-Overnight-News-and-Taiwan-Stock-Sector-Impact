import json
from pathlib import Path
from urllib.parse import urlparse


def test_real_rss_example_config_has_required_schema():
    path = Path("data/fixtures/rss_feeds_real.example.json")

    feeds = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(feeds, list)
    assert feeds
    for feed in feeds:
        assert set(feed) >= {"source", "url", "notes"}
        assert feed["source"].strip()
        assert feed["notes"].strip()

        parsed = urlparse(feed["url"])
        assert parsed.scheme in {"http", "https"}
        assert parsed.netloc


def test_real_rss_example_config_documents_metadata_only_boundary():
    path = Path("data/fixtures/rss_feeds_real.example.json")

    feeds = json.loads(path.read_text(encoding="utf-8"))

    notes = " ".join(feed["notes"].lower() for feed in feeds)
    assert "metadata" in notes
    assert "snippet" in notes
    assert "article bodies" in notes or "article body" in notes
    assert "scrape" in notes or "scraping" in notes


def test_real_rss_example_config_marks_google_news_as_experimental_aggregator():
    path = Path("data/fixtures/rss_feeds_real.example.json")

    feeds = json.loads(path.read_text(encoding="utf-8"))
    google_feeds = [feed for feed in feeds if "news.google.com" in feed["url"]]

    assert google_feeds
    for feed in google_feeds:
        notes = feed["notes"].lower()
        assert "experimental aggregator" in notes
