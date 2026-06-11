"""Deterministic Taiwan pre-market Markdown research report generator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.reporting.io import save_markdown_report


PROJECT_NAME = "AI Pre-Market Briefing Agent"
REPORT_TITLE = "Taiwan Pre-Market Research Brief"
FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "guaranteed",
    "will rise",
    "will fall",
    "target price",
    "must trade",
]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    for term in sorted(FORBIDDEN_TERMS, key=len, reverse=True):
        pattern = re.compile(re.escape(term), flags=re.IGNORECASE)
        text = pattern.sub("restricted wording", text)
    return re.sub(r"\s+", " ", text)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _report_date(signals_df: pd.DataFrame, candidates_df: pd.DataFrame, report_date: str | None) -> str:
    if report_date:
        return report_date
    for df in (candidates_df, signals_df):
        if "taiwan_trading_date" in df.columns and not df.empty:
            values = sorted(_safe_text(value) for value in df["taiwan_trading_date"].dropna() if _safe_text(value))
            if values:
                return values[0]
    return "unspecified"


def _generated_timestamp(signals_df: pd.DataFrame) -> str:
    if "retrieved_at_utc" in signals_df.columns and not signals_df.empty:
        timestamps = pd.to_datetime(signals_df["retrieved_at_utc"], errors="coerce", utc=True).dropna()
        if not timestamps.empty:
            return timestamps.max().isoformat()
    return "not available"


def _value_counts_text(series: pd.Series, limit: int = 5) -> str:
    if series.empty:
        return "none"
    counts = series.fillna("").astype(str)
    counts = counts[counts.str.strip() != ""].value_counts().head(limit)
    if counts.empty:
        return "none"
    return ", ".join(f"{_safe_text(index)} ({count})" for index, count in counts.items())


def _top_themes_text(theme_summary: list[dict], limit: int = 5) -> str:
    if not theme_summary:
        return "none"
    parts = []
    for row in theme_summary[:limit]:
        parts.append(f"{_safe_text(row['sector'])} / {_safe_text(row['theme'])} ({row['signal_count']})")
    return ", ".join(parts)


def _top_targets_text(candidates_df: pd.DataFrame, limit: int = 5) -> str:
    if candidates_df.empty or "taiwan_target" not in candidates_df.columns:
        return "none"
    counts = candidates_df["taiwan_target"].fillna("").astype(str)
    counts = counts[counts.str.strip() != ""].value_counts().head(limit)
    if counts.empty:
        return "none"
    return ", ".join(f"{_safe_text(index)} ({count})" for index, count in counts.items())


def load_report_inputs(signals_path, candidates_path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load signal and Taiwan impact candidate CSV files."""

    return pd.read_csv(signals_path), pd.read_csv(candidates_path)


def summarize_themes(signals_df: pd.DataFrame) -> list[dict]:
    """Summarize classified U.S. news themes by sector and theme."""

    if signals_df.empty:
        return []

    summaries: list[dict] = []
    grouped = signals_df.groupby(["sector", "theme"], dropna=False, sort=True)
    for (sector, theme), group in grouped:
        headlines = [_safe_text(value) for value in group["title"].dropna().head(3)] if "title" in group else []
        sentiment_labels = sorted(set(_safe_text(value) for value in group.get("sentiment_label", pd.Series(dtype=str)).dropna()))
        summaries.append(
            {
                "sector": _safe_text(sector),
                "theme": _safe_text(theme),
                "signal_count": int(len(group)),
                "sentiment_labels": sentiment_labels,
                "representative_headlines": headlines,
            }
        )

    return sorted(summaries, key=lambda row: (-row["signal_count"], row["sector"], row["theme"]))


def summarize_candidates(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """Sort Taiwan impact candidates for deterministic report display."""

    if candidates_df.empty:
        return candidates_df.copy()

    summary = candidates_df.copy()
    summary["_abs_impact_score"] = summary["impact_score"].apply(lambda value: abs(_to_float(value)))
    summary["_combined_confidence_sort"] = summary["combined_confidence"].apply(_to_float)
    summary = summary.sort_values(
        by=["_abs_impact_score", "_combined_confidence_sort", "taiwan_target", "news_id"],
        ascending=[False, False, True, True],
        kind="mergesort",
    )
    return summary.drop(columns=["_abs_impact_score", "_combined_confidence_sort"])


def _candidate_bullets(candidates_df: pd.DataFrame, limit: int = 10) -> list[str]:
    if candidates_df.empty:
        return ["- No watchlist candidates in this category under current deterministic rules."]

    rows = []
    for _, row in candidates_df.head(limit).iterrows():
        target = _safe_text(row.get("taiwan_target")) or _safe_text(row.get("taiwan_ticker")) or "unmapped"
        sector = _safe_text(row.get("taiwan_sector")) or _safe_text(row.get("sector")) or "not specified"
        direction = _safe_text(row.get("directional_impact_label")) or "not specified"
        confidence = _to_float(row.get("combined_confidence"))
        impact = _to_float(row.get("impact_score"))
        rows.append(
            f"- {target}: {sector}; {direction}; combined confidence {confidence:.3f}; "
            f"impact score {impact:.3f}; requires validation."
        )
    return rows


def _theme_section(theme_summary: list[dict]) -> list[str]:
    lines = ["## Overnight U.S. News Themes", ""]
    if not theme_summary:
        lines.extend(["No classified signals were available.", ""])
        return lines

    for row in theme_summary:
        sentiments = ", ".join(row["sentiment_labels"]) if row["sentiment_labels"] else "not specified"
        lines.append(f"### {_safe_text(row['sector'])} / {_safe_text(row['theme'])}")
        lines.append(f"- Signal count: {row['signal_count']}")
        lines.append(f"- Sentiment labels: {_safe_text(sentiments)}")
        if row["representative_headlines"]:
            lines.append("- Representative headlines:")
            for headline in row["representative_headlines"]:
                lines.append(f"  - {headline}")
        lines.append("")
    return lines


def _watchlist_section(candidates_df: pd.DataFrame) -> list[str]:
    lines = ["## Taiwan Watchlist Candidates", ""]
    if candidates_df.empty:
        lines.extend(["No Taiwan impact candidates were generated.", ""])
        return lines

    sorted_candidates = summarize_candidates(candidates_df)
    lines.append("Taiwan targets are grouped by target type, including ticker, basket, proxy, and unmapped rows, with sector context when available.")
    lines.append("")
    for target_type in ["ticker", "basket", "proxy", "unmapped"]:
        group = sorted_candidates[sorted_candidates["taiwan_target_type"] == target_type]
        lines.append(f"### {_safe_text(target_type)}")
        lines.extend(_candidate_bullets(group, limit=10))
        lines.append("")
    return lines


def _directional_section(candidates_df: pd.DataFrame, label: str, header: str) -> list[str]:
    lines = [f"## {header}", ""]
    if candidates_df.empty:
        lines.extend(["No candidates in this category under current deterministic rules.", ""])
        return lines
    group = summarize_candidates(candidates_df[candidates_df["directional_impact_label"] == label])
    lines.extend(_candidate_bullets(group, limit=10))
    lines.append("")
    return lines


def _review_section(candidates_df: pd.DataFrame) -> list[str]:
    lines = ["## Neutral / Unmapped / Requires Review", ""]
    if candidates_df.empty:
        lines.extend(["No neutral or unmapped candidates were generated.", ""])
        return lines
    group = candidates_df[candidates_df["directional_impact_label"].isin(["neutral", "unmapped"])]
    lines.append("Unmapped means no deterministic seed mapping was found for the parsed U.S. ticker set.")
    lines.extend(_candidate_bullets(summarize_candidates(group), limit=12))
    lines.append("")
    return lines


def _source_provenance_section(signals_df: pd.DataFrame) -> list[str]:
    lines = ["## Source Provenance", ""]
    lines.append("Only metadata and RSS-provided snippets are used; article pages are not scraped.")
    if signals_df.empty:
        lines.extend(["- No source rows were available.", ""])
        return lines

    for _, row in signals_df.sort_values(by=["published_at_utc", "source", "title"], kind="mergesort").iterrows():
        source = _safe_text(row.get("source")) or "unknown source"
        title = _safe_text(row.get("title")) or "untitled"
        url = _safe_text(row.get("url"))
        published = _safe_text(row.get("published_at_utc")) or "missing published timestamp"
        url_text = f" URL: {url}." if url else ""
        lines.append(f"- {source}: {title}. Published UTC: {published}.{url_text}")
    lines.append("")
    return lines


def _limitations_section() -> list[str]:
    return [
        "## Limitations",
        "",
        "- Classification is rule-based and deterministic.",
        "- Taiwan mapping uses deterministic seed relationships only.",
        "- No market validation has been run yet.",
        "- Timestamp quality and source availability may affect interpretation.",
        "- This brief is not investment advice and is for research use only.",
        "",
        "## Next Research Step",
        "",
        "Phase 6 will add market data and backtest validation for these research candidates.",
        "",
    ]


def render_markdown_report(
    signals_df: pd.DataFrame,
    candidates_df: pd.DataFrame,
    report_date: str | None = None,
) -> str:
    """Render a deterministic Markdown research brief."""

    date_text = _report_date(signals_df, candidates_df, report_date)
    generated_timestamp = _generated_timestamp(signals_df)
    theme_summary = summarize_themes(signals_df)
    candidate_summary = summarize_candidates(candidates_df)
    dominant_directions = _value_counts_text(candidate_summary.get("directional_impact_label", pd.Series(dtype=str)))

    lines = [
        f"# {REPORT_TITLE}",
        "",
        f"- Report date: {_safe_text(date_text)}",
        f"- Generated timestamp: {_safe_text(generated_timestamp)}",
        f"- Project: {PROJECT_NAME}",
        "- Input basis: Data rows are rendered from the supplied signals CSV and Taiwan impact candidates CSV; no LLM generation is used.",
        "- Research disclaimer: This deterministic brief is not investment advice. Outputs are research signals that require validation.",
        "",
        "## Executive Summary",
        "",
        f"- Classified signals: {len(signals_df)}",
        f"- Mapped Taiwan impact candidates: {len(candidates_df)}",
        f"- Top themes: {_safe_text(_top_themes_text(theme_summary))}",
        f"- Dominant directional labels: {_safe_text(dominant_directions)}",
        "- Directional vocabulary: potentially positive, potentially negative, neutral, unmapped, and irrelevant.",
        "- Summary: Deterministic rules produced watchlist candidates and review items from overnight U.S. metadata. These outputs require validation before research interpretation.",
        "",
    ]

    lines.extend(_theme_section(theme_summary))
    lines.extend(_watchlist_section(candidate_summary))
    lines.extend(_directional_section(candidate_summary, "potentially_positive", "Potentially Positive Candidates"))
    lines.extend(_directional_section(candidate_summary, "potentially_negative", "Potentially Negative Candidates"))
    lines.extend(_review_section(candidate_summary))
    lines.extend(_source_provenance_section(signals_df))
    lines.extend(_limitations_section())

    markdown = "\n".join(lines).strip() + "\n"
    lowered = markdown.lower()
    blocked = [term for term in FORBIDDEN_TERMS if term in lowered]
    if blocked:
        raise ValueError(f"Report contains restricted wording: {', '.join(blocked)}")
    return markdown


def generate_report(signals_path, candidates_path, output_path, report_date: str | None = None) -> str:
    """Load inputs, render Markdown, save it, and return the saved path."""

    signals_df, candidates_df = load_report_inputs(signals_path, candidates_path)
    markdown = render_markdown_report(signals_df, candidates_df, report_date=report_date)
    path = save_markdown_report(markdown, output_path)
    return str(path)
