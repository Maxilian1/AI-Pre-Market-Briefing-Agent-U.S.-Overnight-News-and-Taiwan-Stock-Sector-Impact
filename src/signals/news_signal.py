"""Structured rule-based news signal schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass


def _serialize_list(values: list[str]) -> str:
    return "|".join(values)


@dataclass(frozen=True)
class NewsSignal:
    """One metadata-derived research feature row.

    This is a deterministic classification artifact, not a trading
    recommendation and not a Taiwan ticker impact mapping.
    """

    news_id: str
    duplicate_group_id: str | None
    source: str
    title: str
    url: str | None
    published_at_utc: str | None
    retrieved_at_utc: str
    taiwan_trading_date: str | None
    sector: str
    theme: str
    us_tickers: list[str]
    sentiment_label: str
    sentiment_score: float
    relevance_label: str
    relevance_score: float
    confidence: float
    classification_method: str
    matched_rules: list[str]
    reasoning_short: str

    def to_dict(self) -> dict[str, str | float | None]:
        row = asdict(self)
        row["us_tickers"] = _serialize_list(self.us_tickers)
        row["matched_rules"] = _serialize_list(self.matched_rules)
        return row
