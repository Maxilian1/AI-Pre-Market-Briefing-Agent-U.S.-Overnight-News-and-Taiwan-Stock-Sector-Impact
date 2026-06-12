"""Text cleaning for rule-based classification inputs."""

from __future__ import annotations

import html
import re


URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
HREF_ATTR_PATTERN = re.compile(r"\s+href\s*=\s*(['\"]).*?\1", flags=re.IGNORECASE | re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")
GOOGLE_NEWS_ARTIFACT_PATTERN = re.compile(
    r"\b(?:news\.google\.com|google\.com/rss|rss/articles|google news)\b",
    flags=re.IGNORECASE,
)


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_html_preserving_visible_text(value: str | None) -> str:
    """Remove tags, href URLs, URL strings, and decode visible text."""

    if value is None:
        return ""
    text = html.unescape(str(value))
    text = HREF_ATTR_PATTERN.sub("", text)
    text = URL_PATTERN.sub(" ", text)
    text = TAG_PATTERN.sub(" ", text)
    text = GOOGLE_NEWS_ARTIFACT_PATTERN.sub(" ", text)
    return _collapse_whitespace(text)


def clean_google_news_summary(raw_summary: str | None) -> str:
    """Clean Google News RSS-style HTML summaries for classification."""

    cleaned = strip_html_preserving_visible_text(raw_summary)
    cleaned = GOOGLE_NEWS_ARTIFACT_PATTERN.sub(" ", cleaned)
    return _collapse_whitespace(cleaned)


def build_classification_text(title: str, raw_summary: str | None) -> str:
    """Build classification text from title and cleaned summary only.

    Source names, feed names, URLs, canonical URLs, and provider labels are not
    included by design.
    """

    title_text = strip_html_preserving_visible_text(title)
    summary_text = clean_google_news_summary(raw_summary)
    return _collapse_whitespace(" ".join(part for part in [title_text, summary_text] if part))
