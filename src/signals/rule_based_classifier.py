"""Deterministic Phase 3 rule-based news classifier."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from src.news_collectors.dedupe import normalize_title
from src.signals.news_signal import NewsSignal
from src.signals.rules import (
    CLASSIFICATION_METHOD,
    NEGATIVE_KEYWORDS,
    NEUTRAL_KEYWORDS,
    POSITIVE_KEYWORDS,
    SECTOR_KEYWORDS,
    SECTOR_PRIORITY,
    THEME_KEYWORDS,
    THEME_PRIORITY,
    TICKER_KEYWORDS,
)
from src.time_utils import assign_taiwan_trading_date


OUTPUT_COLUMNS = [
    "news_id",
    "duplicate_group_id",
    "source",
    "title",
    "url",
    "published_at_utc",
    "retrieved_at_utc",
    "taiwan_trading_date",
    "sector",
    "theme",
    "us_tickers",
    "sentiment_label",
    "sentiment_score",
    "relevance_label",
    "relevance_score",
    "confidence",
    "classification_method",
    "matched_rules",
    "reasoning_short",
]


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    return text or None


def _text_for_matching(title: str, raw_summary: str | None = None) -> str:
    parts = [title]
    if raw_summary:
        parts.append(raw_summary)
    return normalize_title(" ".join(parts))


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_title(keyword)
    if not normalized_keyword:
        return False
    pattern = r"(?<!\w)" + re.escape(normalized_keyword).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text) is not None


def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if _contains_keyword(text, keyword)]


def _pick_first_by_priority(matches: dict[str, list[str]], priority: list[str]) -> str | None:
    for name in priority:
        if matches.get(name):
            return name
    for name, values in matches.items():
        if values:
            return name
    return None


def _sentiment(text: str, is_relevant: bool) -> tuple[str, float, list[str]]:
    if not is_relevant:
        return "irrelevant", 0.0, []

    positive_matches = _matched_keywords(text, POSITIVE_KEYWORDS)
    negative_matches = _matched_keywords(text, NEGATIVE_KEYWORDS)
    neutral_matches = _matched_keywords(text, NEUTRAL_KEYWORDS)
    rules = [f"sentiment:positive:{keyword}" for keyword in positive_matches]
    rules.extend(f"sentiment:negative:{keyword}" for keyword in negative_matches)
    rules.extend(f"sentiment:neutral:{keyword}" for keyword in neutral_matches)

    if positive_matches and negative_matches:
        return "mixed", 0.0, rules
    if positive_matches:
        return "positive", 0.7, rules
    if negative_matches:
        return "negative", -0.7, rules
    return "neutral", 0.0, rules


def _relevance(sector: str, theme: str, tickers: list[str]) -> tuple[str, float]:
    if sector == "Irrelevant":
        return "irrelevant", 0.0
    if sector in {"Macro", "Energy"}:
        return "low", 0.3
    if tickers and theme != "irrelevant":
        return "high", 0.9
    if tickers or theme != "irrelevant":
        return "medium", 0.6
    return "low", 0.3


def _confidence(relevance_score: float, matched_rule_count: int) -> float:
    if relevance_score == 0:
        return 0.3
    return round(min(1.0, 0.35 + relevance_score * 0.45 + matched_rule_count * 0.03), 3)


def _reasoning(
    tickers: list[str],
    theme: str,
    sector: str,
    sentiment_label: str,
) -> str:
    if sector == "Irrelevant":
        return "No semiconductor, AI infrastructure, macro, or energy keywords matched; classified as irrelevant."

    ticker_text = ", ".join(tickers) if tickers else "no specific U.S. ticker"
    return (
        f"Matched {ticker_text} and {theme} keywords; classified as "
        f"{sector} with {sentiment_label} sentiment for research use."
    )


def classify_headline(title: str, raw_summary: str | None = None) -> dict:
    """Classify a headline/snippet into deterministic research labels."""

    text = _text_for_matching(title, raw_summary)
    matched_rules: list[str] = []

    ticker_matches = {
        ticker: _matched_keywords(text, keywords)
        for ticker, keywords in TICKER_KEYWORDS.items()
    }
    tickers = [ticker for ticker, matches in ticker_matches.items() if matches]
    for ticker, matches in ticker_matches.items():
        matched_rules.extend(f"ticker:{ticker}:{keyword}" for keyword in matches)

    sector_matches = {
        sector: _matched_keywords(text, keywords)
        for sector, keywords in SECTOR_KEYWORDS.items()
    }
    sector = _pick_first_by_priority(sector_matches, SECTOR_PRIORITY) or "Irrelevant"
    for matched_sector, matches in sector_matches.items():
        matched_rules.extend(f"sector:{matched_sector}:{keyword}" for keyword in matches)

    theme_matches = {
        theme: _matched_keywords(text, keywords)
        for theme, keywords in THEME_KEYWORDS.items()
    }
    theme = _pick_first_by_priority(theme_matches, THEME_PRIORITY) or "irrelevant"
    for matched_theme, matches in theme_matches.items():
        matched_rules.extend(f"theme:{matched_theme}:{keyword}" for keyword in matches)

    is_relevant = sector != "Irrelevant"
    sentiment_label, sentiment_score, sentiment_rules = _sentiment(text, is_relevant)
    matched_rules.extend(sentiment_rules)
    relevance_label, relevance_score = _relevance(sector, theme, tickers)
    confidence = _confidence(relevance_score, len(matched_rules))
    reasoning_short = _reasoning(tickers, theme, sector, sentiment_label)

    return {
        "sector": sector,
        "theme": theme,
        "us_tickers": tickers,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "relevance_label": relevance_label,
        "relevance_score": relevance_score,
        "confidence": confidence,
        "classification_method": CLASSIFICATION_METHOD,
        "matched_rules": matched_rules,
        "reasoning_short": reasoning_short,
    }


def _assign_taiwan_trading_date(row: dict) -> str | None:
    timestamp = _clean_optional(row.get("published_at_utc")) or _clean_optional(row.get("retrieved_at_utc"))
    if timestamp is None:
        return None
    try:
        return assign_taiwan_trading_date(timestamp).isoformat()
    except (TypeError, ValueError):
        return None


def classify_news_row(row: dict) -> NewsSignal:
    """Classify one raw news CSV row into a NewsSignal."""

    title = _clean_optional(row.get("title")) or ""
    raw_summary = _clean_optional(row.get("raw_summary"))
    classification = classify_headline(title, raw_summary=raw_summary)

    return NewsSignal(
        news_id=_clean_optional(row.get("news_id")) or "",
        duplicate_group_id=_clean_optional(row.get("duplicate_group_id")),
        source=_clean_optional(row.get("source")) or "",
        title=title,
        url=_clean_optional(row.get("url")),
        published_at_utc=_clean_optional(row.get("published_at_utc")),
        retrieved_at_utc=_clean_optional(row.get("retrieved_at_utc")) or "",
        taiwan_trading_date=_assign_taiwan_trading_date(row),
        sector=classification["sector"],
        theme=classification["theme"],
        us_tickers=classification["us_tickers"],
        sentiment_label=classification["sentiment_label"],
        sentiment_score=classification["sentiment_score"],
        relevance_label=classification["relevance_label"],
        relevance_score=classification["relevance_score"],
        confidence=classification["confidence"],
        classification_method=classification["classification_method"],
        matched_rules=classification["matched_rules"],
        reasoning_short=classification["reasoning_short"],
    )


def _dedupe_raw_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "duplicate_group_id" not in df.columns:
        return df.copy()

    working = df.copy()
    working["_original_index"] = range(len(working))
    duplicate_group = working["duplicate_group_id"].fillna("").astype(str).str.strip()
    no_group = working[duplicate_group == ""].copy()
    grouped = working[duplicate_group != ""].copy()

    if grouped.empty:
        return working.drop(columns=["_original_index"])

    grouped["_published_sort"] = pd.to_datetime(grouped.get("published_at_utc"), errors="coerce", utc=True)
    grouped["_published_missing"] = grouped["_published_sort"].isna()
    for column in ("retrieved_at_utc", "news_id"):
        if column not in grouped.columns:
            grouped[column] = ""

    representatives = (
        grouped.sort_values(
            by=[
                "duplicate_group_id",
                "_published_missing",
                "_published_sort",
                "retrieved_at_utc",
                "news_id",
                "_original_index",
            ],
            kind="mergesort",
        )
        .drop_duplicates(subset=["duplicate_group_id"], keep="first")
        .drop(columns=["_published_sort", "_published_missing"])
    )

    deduped = pd.concat([no_group, representatives], ignore_index=True)
    deduped = deduped.sort_values("_original_index", kind="mergesort")
    return deduped.drop(columns=["_original_index"]).reset_index(drop=True)


def classify_news_dataframe(df: pd.DataFrame, keep_duplicates: bool = False) -> pd.DataFrame:
    """Classify raw news rows, dropping duplicate groups by default."""

    input_df = df.copy()
    if not keep_duplicates:
        input_df = _dedupe_raw_dataframe(input_df)

    rows = [classify_news_row(row.to_dict()).to_dict() for _, row in input_df.iterrows()]
    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
