from src.signals.text_cleaning import (
    build_classification_text,
    clean_google_news_summary,
    strip_html_preserving_visible_text,
)


def test_strip_html_removes_href_urls_and_decodes_entities():
    raw = '<a href="https://news.google.com/rss/articles/x">Oil&nbsp;prices</a>'

    cleaned = strip_html_preserving_visible_text(raw)

    assert cleaned == "Oil prices"
    assert "news.google.com" not in cleaned.lower()
    assert "https://" not in cleaned.lower()


def test_google_news_anchor_only_does_not_add_google_provider_signal():
    raw = '<a href="https://news.google.com/rss/articles/x">Oil prices steady</a> Google News'

    cleaned = clean_google_news_summary(raw)

    assert "google" not in cleaned.lower()
    assert "news.google.com" not in cleaned.lower()
    assert "Oil prices steady" in cleaned


def test_build_classification_text_uses_title_and_cleaned_summary_only():
    text = build_classification_text(
        "Fed officials discuss rate outlook",
        '<a href="https://news.google.com/rss/articles/x">Fed outlook</a>',
    )

    assert "Fed officials discuss rate outlook" in text
    assert "Fed outlook" in text
    assert "news.google.com" not in text.lower()
