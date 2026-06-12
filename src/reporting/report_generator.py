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
MARKET_CONTEXT_SECTORS = {"Macro", "Energy"}
MARKET_CONTEXT_THEMES = {"interest rates / Fed", "oil / energy"}
REQUIRED_REPORT_SECTIONS = [
    "Executive Summary",
    "Overnight U.S. News Themes",
    "Market Context Signals",
    "Taiwan Watchlist Candidates",
    "Potentially Positive Candidates",
    "Potentially Negative Candidates",
    "Neutral / Unmapped / Requires Review",
    "Source Provenance",
    "Limitations",
    "Next Research Step",
]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def _external_headline(value: Any) -> str:
    return _safe_text(value) or "untitled"


def _forbidden_pattern(term: str) -> re.Pattern:
    if " " in term:
        return re.compile(re.escape(term), flags=re.IGNORECASE)
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", flags=re.IGNORECASE)


def _generated_commentary_violations(markdown: str) -> list[str]:
    violations: list[str] = []
    for line in markdown.splitlines():
        if "External headline:" in line:
            continue
        for term in FORBIDDEN_TERMS:
            if _forbidden_pattern(term).search(line):
                violations.append(term)
    return sorted(set(violations))


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
        headlines = [_external_headline(value) for value in group["title"].dropna().head(3)] if "title" in group else []
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


def _is_market_context_row(row: pd.Series | dict) -> bool:
    sector = _safe_text(row.get("sector"))
    theme = _safe_text(row.get("theme"))
    return sector in MARKET_CONTEXT_SECTORS or theme in MARKET_CONTEXT_THEMES


def _candidate_report_category(row: pd.Series | dict) -> str:
    direction = _safe_text(row.get("directional_impact_label"))
    target_type = _safe_text(row.get("taiwan_target_type"))
    sector = _safe_text(row.get("sector"))
    relevance = _safe_text(row.get("relevance_label"))

    if direction == "irrelevant" or sector == "Irrelevant" or relevance == "irrelevant":
        return "irrelevant"
    if _is_market_context_row(row):
        return "market_context"
    if target_type == "unmapped" or direction == "unmapped":
        return "unmapped_relevant_equity_signal"
    return target_type or "unmapped_relevant_equity_signal"


def _reportable_candidates(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df.empty:
        return candidates_df.copy()
    working = candidates_df.copy()
    working["_report_category"] = working.apply(_candidate_report_category, axis=1)
    return working


def aggregate_candidates(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate Taiwan candidates by target and directional label for report display."""

    if candidates_df.empty:
        return pd.DataFrame(
            columns=[
                "taiwan_target",
                "taiwan_target_type",
                "taiwan_ticker",
                "taiwan_company",
                "taiwan_sector",
                "directional_impact_label",
                "candidate_count",
                "mean_impact_score",
                "max_abs_impact_score",
                "mean_combined_confidence",
                "representative_headlines",
                "_report_category",
            ]
        )

    working = _reportable_candidates(candidates_df)
    working["_impact_score_float"] = working["impact_score"].apply(_to_float)
    working["_combined_confidence_float"] = working["combined_confidence"].apply(_to_float)
    working["_abs_impact_score"] = working["_impact_score_float"].abs()
    group_columns = [
        "taiwan_target",
        "taiwan_ticker",
        "taiwan_company",
        "taiwan_sector",
        "directional_impact_label",
        "_report_category",
    ]
    for column in group_columns + ["taiwan_target_type", "_report_category", "title", "news_id"]:
        if column not in working.columns:
            working[column] = ""
    working[group_columns] = working[group_columns].fillna("")

    rows: list[dict] = []
    grouped = working.groupby(group_columns, dropna=False, sort=True)
    for group_key, group in grouped:
        sorted_group = group.sort_values(
            by=["_abs_impact_score", "_combined_confidence_float", "news_id"],
            ascending=[False, False, True],
            kind="mergesort",
        )
        headlines: list[str] = []
        for headline in sorted_group["title"]:
            text = _external_headline(headline)
            if text not in headlines:
                headlines.append(text)
            if len(headlines) == 2:
                break
        first = sorted_group.iloc[0]
        rows.append(
            {
                "taiwan_target": _safe_text(group_key[0]) or "unmapped",
                "taiwan_ticker": _safe_text(group_key[1]),
                "taiwan_company": _safe_text(group_key[2]),
                "taiwan_sector": _safe_text(group_key[3]) or _safe_text(first.get("sector")) or "not specified",
                "directional_impact_label": _safe_text(group_key[4]) or "not specified",
                "taiwan_target_type": _safe_text(first.get("taiwan_target_type")) or "unmapped",
                "_report_category": _safe_text(group_key[5]) or "unmapped_relevant_equity_signal",
                "candidate_count": int(len(group)),
                "mean_impact_score": round(float(group["_impact_score_float"].mean()), 6),
                "max_abs_impact_score": round(float(group["_abs_impact_score"].max()), 6),
                "mean_combined_confidence": round(float(group["_combined_confidence_float"].mean()), 6),
                "representative_headlines": headlines,
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values(
        by=["max_abs_impact_score", "mean_combined_confidence", "candidate_count", "taiwan_target"],
        ascending=[False, False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def _candidate_bullets(candidates_df: pd.DataFrame, limit: int = 10) -> list[str]:
    if candidates_df.empty:
        return ["- No watchlist candidates in this category under current deterministic rules."]

    rows = []
    for _, row in candidates_df.head(limit).iterrows():
        target = _safe_text(row.get("taiwan_target")) or _safe_text(row.get("taiwan_ticker")) or "unmapped"
        sector = _safe_text(row.get("taiwan_sector")) or _safe_text(row.get("sector")) or "not specified"
        direction = _safe_text(row.get("directional_impact_label")) or "not specified"
        if "candidate_count" in row.index:
            confidence = _to_float(row.get("mean_combined_confidence"))
            impact = _to_float(row.get("mean_impact_score"))
            max_abs = _to_float(row.get("max_abs_impact_score"))
            rows.append(
                f"- {target}: {sector}; {direction}; candidate_count {int(row.get('candidate_count', 0))}; "
                f"mean impact score {impact:.3f}; max abs impact score {max_abs:.3f}; "
                f"mean combined confidence {confidence:.3f}; requires validation."
            )
            for headline in row.get("representative_headlines", []) or []:
                rows.append(f"  - External headline: {_external_headline(headline)}")
        else:
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
                lines.append(f"  - External headline: {headline}")
        lines.append("")
    return lines


def _market_context_section(signals_df: pd.DataFrame) -> list[str]:
    lines = ["## Market Context Signals", ""]
    lines.append("These are market context signals and are not direct Taiwan company mappings.")
    lines.append("")

    if signals_df.empty:
        lines.extend(["No market context signals were available.", ""])
        return lines

    context_df = signals_df[
        signals_df["sector"].isin(MARKET_CONTEXT_SECTORS)
        | signals_df["theme"].isin(MARKET_CONTEXT_THEMES)
    ].copy()
    if context_df.empty:
        lines.extend(["No Macro or Energy context signals were classified.", ""])
        return lines

    for sector, theme in [("Macro", "interest rates / Fed"), ("Energy", "oil / energy")]:
        group = context_df[(context_df["sector"] == sector) | (context_df["theme"] == theme)]
        lines.append(f"### {sector} / {theme}")
        lines.append(f"- Signal count: {len(group)}")
        if group.empty:
            lines.append("- No examples in this run.")
        else:
            lines.append("- Representative external headlines:")
            for headline in group["title"].dropna().head(3):
                lines.append(f"  - External headline: {_external_headline(headline)}")
        lines.append("")
    return lines


def _watchlist_section(aggregated_candidates_df: pd.DataFrame) -> list[str]:
    lines = ["## Taiwan Watchlist Candidates", ""]
    if aggregated_candidates_df.empty:
        lines.extend(["No Taiwan impact candidates were generated.", ""])
        return lines

    sorted_candidates = aggregated_candidates_df.copy()
    lines.append("Taiwan targets are aggregated by target, Taiwan ticker, sector, and directional label. Market context items are summarized separately above.")
    lines.append("")
    category_labels = [
        ("ticker", "ticker"),
        ("basket", "basket"),
        ("proxy", "proxy"),
        ("unmapped_relevant_equity_signal", "unmapped / review"),
    ]
    for category, label in category_labels:
        group = sorted_candidates[sorted_candidates["_report_category"] == category]
        lines.append(f"### {_safe_text(label)}")
        lines.extend(_candidate_bullets(group, limit=10))
        lines.append("")
    return lines


def _direct_candidate_groups(aggregated_candidates_df: pd.DataFrame) -> pd.DataFrame:
    if aggregated_candidates_df.empty:
        return aggregated_candidates_df.copy()
    return aggregated_candidates_df[
        ~aggregated_candidates_df["_report_category"].isin(["market_context", "irrelevant"])
    ].copy()


def _directional_section(aggregated_candidates_df: pd.DataFrame, label: str, header: str) -> list[str]:
    lines = [f"## {header}", ""]
    if aggregated_candidates_df.empty:
        lines.extend(["No candidates in this category under current deterministic rules.", ""])
        return lines
    group = _direct_candidate_groups(aggregated_candidates_df)
    group = group[group["directional_impact_label"] == label]
    lines.extend(_candidate_bullets(group, limit=10))
    lines.append("")
    return lines


def _review_section(aggregated_candidates_df: pd.DataFrame) -> list[str]:
    lines = ["## Neutral / Unmapped / Requires Review", ""]
    if aggregated_candidates_df.empty:
        lines.extend(["No neutral or unmapped candidates were generated.", ""])
        return lines
    direct = _direct_candidate_groups(aggregated_candidates_df)
    neutral = direct[direct["directional_impact_label"] == "neutral"]
    unmapped = direct[direct["_report_category"] == "unmapped_relevant_equity_signal"]
    market_context_count = int((aggregated_candidates_df["_report_category"] == "market_context").sum())
    irrelevant_count = int((aggregated_candidates_df["_report_category"] == "irrelevant").sum())
    lines.append("Unmapped means no deterministic seed mapping was found for the parsed U.S. ticker set.")
    lines.append(f"Market context candidate groups summarized above: {market_context_count}")
    lines.append(f"Irrelevant candidate groups omitted from Taiwan impact lists: {irrelevant_count}")
    lines.append("")
    lines.append("### Neutral mapped candidates")
    lines.extend(_candidate_bullets(neutral, limit=10))
    lines.append("")
    lines.append("### Unmapped relevant equity signals")
    lines.extend(_candidate_bullets(unmapped, limit=10))
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
        title = _external_headline(row.get("title"))
        url = _safe_text(row.get("url"))
        published = _safe_text(row.get("published_at_utc")) or "missing published timestamp"
        url_text = f" URL: {url}." if url else ""
        lines.append(f"- {source}: External headline: {title}. Published UTC: {published}.{url_text}")
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
    sorted_candidates = summarize_candidates(candidates_df)
    candidate_summary = aggregate_candidates(sorted_candidates)
    dominant_directions = _value_counts_text(sorted_candidates.get("directional_impact_label", pd.Series(dtype=str)))

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
    lines.extend(_market_context_section(signals_df))
    lines.extend(_watchlist_section(candidate_summary))
    lines.extend(_directional_section(candidate_summary, "potentially_positive", "Potentially Positive Candidates"))
    lines.extend(_directional_section(candidate_summary, "potentially_negative", "Potentially Negative Candidates"))
    lines.extend(_review_section(candidate_summary))
    lines.extend(_source_provenance_section(signals_df))
    lines.extend(_limitations_section())

    markdown = "\n".join(lines).strip() + "\n"
    blocked = _generated_commentary_violations(markdown)
    if blocked:
        raise ValueError(f"Report contains restricted wording: {', '.join(blocked)}")
    return markdown


def generate_report(signals_path, candidates_path, output_path, report_date: str | None = None) -> str:
    """Load inputs, render Markdown, save it, and return the saved path."""

    signals_df, candidates_df = load_report_inputs(signals_path, candidates_path)
    markdown = render_markdown_report(signals_df, candidates_df, report_date=report_date)
    path = save_markdown_report(markdown, output_path)
    return str(path)
