"""Deterministic Taiwan target mapping from rule-based U.S. news signals."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import PROCESSED_DATA_DIR


MAPPING_METHOD = "seed_mapping_v1"
DEFAULT_MAPPING_PATH = PROCESSED_DATA_DIR / "ticker_mapping_seed.csv"

CONFIDENCE_MAP = {
    "high": 0.9,
    "medium": 0.6,
    "low": 0.3,
}

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
    "signal_confidence",
    "taiwan_target",
    "taiwan_target_type",
    "taiwan_ticker",
    "taiwan_company",
    "taiwan_sector",
    "relationship_type",
    "mapping_confidence",
    "assumption_flag",
    "mapping_notes",
    "directional_impact_label",
    "impact_score",
    "combined_confidence",
    "mapping_method",
    "reasoning_short",
]


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    return text or None


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _mapping_confidence(value: Any) -> float:
    text = _clean_optional(value)
    if text is None:
        return 0.0
    lowered = text.lower()
    if lowered in CONFIDENCE_MAP:
        return CONFIDENCE_MAP[lowered]
    return _clamp(_to_float(text), 0.0, 1.0)


def _signal_metadata(signal_row: dict) -> dict:
    return {
        "news_id": _clean_optional(signal_row.get("news_id")) or "",
        "duplicate_group_id": _clean_optional(signal_row.get("duplicate_group_id")),
        "source": _clean_optional(signal_row.get("source")) or "",
        "title": _clean_optional(signal_row.get("title")) or "",
        "url": _clean_optional(signal_row.get("url")),
        "published_at_utc": _clean_optional(signal_row.get("published_at_utc")),
        "retrieved_at_utc": _clean_optional(signal_row.get("retrieved_at_utc")) or "",
        "taiwan_trading_date": _clean_optional(signal_row.get("taiwan_trading_date")),
        "sector": _clean_optional(signal_row.get("sector")) or "",
        "theme": _clean_optional(signal_row.get("theme")) or "",
        "us_tickers": "|".join(parse_pipe_or_json_list(signal_row.get("us_tickers"))),
        "sentiment_label": _clean_optional(signal_row.get("sentiment_label")) or "",
        "sentiment_score": _to_float(signal_row.get("sentiment_score")),
        "relevance_label": _clean_optional(signal_row.get("relevance_label")) or "",
        "relevance_score": _to_float(signal_row.get("relevance_score")),
        "signal_confidence": _to_float(signal_row.get("confidence")),
    }


def load_mapping_table(path=None) -> pd.DataFrame:
    """Load the deterministic seed mapping table."""

    mapping_path = Path(path) if path else DEFAULT_MAPPING_PATH
    return pd.read_csv(mapping_path)


def parse_pipe_or_json_list(value) -> list[str]:
    """Parse Phase 3 ticker serialization as pipe-delimited or JSON-like."""

    if value is None:
        return []
    if isinstance(value, float) and math.isnan(value):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(text)
            except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]

    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]

    return [text]


def determine_target_type(taiwan_ticker: str) -> str:
    """Classify seed target markers without inventing relationships."""

    ticker = _clean_optional(taiwan_ticker)
    if ticker is None:
        return "unmapped"
    if ticker.startswith("BASKET:"):
        return "basket"
    if ticker.startswith("PROXY:"):
        return "proxy"
    if ticker.endswith(".TW"):
        return "ticker"
    return "unmapped"


def _directional_impact_label(signal_row: dict, has_mapping: bool = True) -> str:
    sector = _clean_optional(signal_row.get("sector"))
    relevance_label = _clean_optional(signal_row.get("relevance_label"))
    relevance_score = _to_float(signal_row.get("relevance_score"))
    sentiment_label = _clean_optional(signal_row.get("sentiment_label"))

    if sector == "Irrelevant" or relevance_label == "irrelevant":
        return "irrelevant"
    if not has_mapping:
        return "unmapped"
    if sentiment_label == "positive" and relevance_score > 0:
        return "potentially_positive"
    if sentiment_label == "negative" and relevance_score > 0:
        return "potentially_negative"
    if sentiment_label in {"neutral", "mixed"}:
        return "neutral"
    return "neutral"


def _mapped_reasoning(signal_row: dict, mapping_row: dict, directional_label: str) -> str:
    us_ticker = _clean_optional(mapping_row.get("us_ticker")) or "unknown U.S. ticker"
    taiwan_ticker = _clean_optional(mapping_row.get("taiwan_ticker")) or "unmapped target"
    relationship = _clean_optional(mapping_row.get("relationship_type")) or "seed relationship"
    sentiment = _clean_optional(signal_row.get("sentiment_label")) or "unknown"
    return (
        f"Deterministic seed mapping matched {us_ticker} to {taiwan_ticker} via "
        f"{relationship}; directional label is {directional_label} based on {sentiment} sentiment."
    )


def _unmapped_reasoning(signal_row: dict) -> str:
    tickers = parse_pipe_or_json_list(signal_row.get("us_tickers"))
    ticker_text = ", ".join(tickers) if tickers else "no parsed U.S. tickers"
    return (
        f"No deterministic seed mapping was found for {ticker_text}; row remains unmapped "
        "for research review."
    )


def _irrelevant_reasoning(signal_row: dict) -> str:
    return "Signal is classified as irrelevant, so no Taiwan mapping candidate is created by default."


def _target_name(mapping_row: dict, target_type: str) -> str:
    ticker = _clean_optional(mapping_row.get("taiwan_ticker")) or ""
    company = _clean_optional(mapping_row.get("taiwan_company")) or ""
    if target_type == "ticker":
        return f"{ticker} {company}".strip()
    return company or ticker


def _mapping_output_row(signal_row: dict, mapping_row: dict) -> dict:
    signal = _signal_metadata(signal_row)
    mapping_confidence = _mapping_confidence(mapping_row.get("confidence"))
    target_type = determine_target_type(str(mapping_row.get("taiwan_ticker", "")))
    directional_label = _directional_impact_label(signal_row, has_mapping=True)
    impact_score = _clamp(signal["sentiment_score"] * signal["relevance_score"] * mapping_confidence, -1.0, 1.0)
    combined_confidence = _clamp(signal["signal_confidence"] * mapping_confidence, 0.0, 1.0)

    return {
        **signal,
        "taiwan_target": _target_name(mapping_row, target_type),
        "taiwan_target_type": target_type,
        "taiwan_ticker": _clean_optional(mapping_row.get("taiwan_ticker")) or "",
        "taiwan_company": _clean_optional(mapping_row.get("taiwan_company")) or "",
        "taiwan_sector": _clean_optional(mapping_row.get("taiwan_sector")) or "",
        "relationship_type": _clean_optional(mapping_row.get("relationship_type")) or "",
        "mapping_confidence": round(mapping_confidence, 6),
        "assumption_flag": _clean_optional(mapping_row.get("assumption_flag")) or "",
        "mapping_notes": _clean_optional(mapping_row.get("notes")) or "",
        "directional_impact_label": directional_label,
        "impact_score": round(impact_score, 6),
        "combined_confidence": round(combined_confidence, 6),
        "mapping_method": MAPPING_METHOD,
        "reasoning_short": _mapped_reasoning(signal_row, mapping_row, directional_label),
    }


def _unmapped_output_row(signal_row: dict) -> dict:
    signal = _signal_metadata(signal_row)
    return {
        **signal,
        "taiwan_target": "unmapped",
        "taiwan_target_type": "unmapped",
        "taiwan_ticker": "",
        "taiwan_company": "",
        "taiwan_sector": "",
        "relationship_type": "",
        "mapping_confidence": 0.0,
        "assumption_flag": "",
        "mapping_notes": "",
        "directional_impact_label": "unmapped",
        "impact_score": 0.0,
        "combined_confidence": 0.0,
        "mapping_method": MAPPING_METHOD,
        "reasoning_short": _unmapped_reasoning(signal_row),
    }


def _irrelevant_output_row(signal_row: dict) -> dict:
    signal = _signal_metadata(signal_row)
    return {
        **signal,
        "taiwan_target": "irrelevant",
        "taiwan_target_type": "unmapped",
        "taiwan_ticker": "",
        "taiwan_company": "",
        "taiwan_sector": "",
        "relationship_type": "",
        "mapping_confidence": 0.0,
        "assumption_flag": "",
        "mapping_notes": "",
        "directional_impact_label": "irrelevant",
        "impact_score": 0.0,
        "combined_confidence": 0.0,
        "mapping_method": MAPPING_METHOD,
        "reasoning_short": _irrelevant_reasoning(signal_row),
    }


def map_signal_row(signal_row: dict, mapping_df: pd.DataFrame) -> list[dict]:
    """Map one relevant signal using only seed mapping rows."""

    if _directional_impact_label(signal_row, has_mapping=True) == "irrelevant":
        return []

    tickers = parse_pipe_or_json_list(signal_row.get("us_tickers"))
    if not tickers:
        return [_unmapped_output_row(signal_row)]

    matches = mapping_df[mapping_df["us_ticker"].isin(tickers)].copy()
    if matches.empty:
        return [_unmapped_output_row(signal_row)]

    rows = []
    for _, mapping_row in matches.iterrows():
        rows.append(_mapping_output_row(signal_row, mapping_row.to_dict()))
    return rows


def map_signals_dataframe(
    signals_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
    include_irrelevant: bool = False,
) -> pd.DataFrame:
    """Map a signal table into Taiwan impact candidate rows."""

    rows: list[dict] = []
    for _, signal_row in signals_df.iterrows():
        row_dict = signal_row.to_dict()
        mapped_rows = map_signal_row(row_dict, mapping_df)
        if not mapped_rows and include_irrelevant:
            mapped_rows = [_irrelevant_output_row(row_dict)]
        rows.extend(mapped_rows)

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
