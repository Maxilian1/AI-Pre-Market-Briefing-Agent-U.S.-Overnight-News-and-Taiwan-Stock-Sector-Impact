"""Markdown reporting for Phase 6B event-study diagnostics."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def _fmt(value, digits: int = 6) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.{digits}f}"
    return str(value)


def _markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> list[str]:
    if df.empty:
        return ["No rows available."]
    display = df[columns].head(limit).copy() if limit else df[columns].copy()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in display.iterrows():
        lines.append("| " + " | ".join(_fmt(row.get(column)) for column in columns) + " |")
    return lines


def render_event_study_summary(
    return_labels_df: pd.DataFrame,
    aggregated_df: pd.DataFrame,
    bucket_summary_df: pd.DataFrame,
    directional_hit_ratio_df: pd.DataFrame,
    report_date: str | None = None,
) -> str:
    """Render a deterministic event-study summary."""

    available_count = int(aggregated_df["return_data_available"].fillna(False).astype(bool).sum()) if not aggregated_df.empty else 0
    unavailable_count = int(len(aggregated_df) - available_count)
    label_counts = (
        aggregated_df["final_directional_label"].fillna("").astype(str).value_counts().to_dict()
        if not aggregated_df.empty and "final_directional_label" in aggregated_df.columns
        else {}
    )

    lines: list[str] = [
        "# Event Study Summary",
        "",
        f"- Report date: {report_date or 'unspecified'}",
        f"- Input return label rows: {len(return_labels_df)}",
        f"- Aggregated target-day rows: {len(aggregated_df)}",
        f"- Aggregated rows with available returns: {available_count}",
        f"- Aggregated rows without available returns: {unavailable_count}",
        "- Research disclaimer: This is a research diagnostic, not investment advice.",
        "",
        "## Input Data",
        "",
        "Return label rows are Phase 6A outcome observations joined to deterministic Taiwan impact candidates.",
        "Returns are outcome labels and were not used to generate signals.",
        "",
        "## Aggregation Method",
        "",
        "News-candidate rows are aggregated before statistics by Taiwan trading date, return target, return target type, and Taiwan target type. Taiwan sector is summarized after grouping.",
        "The final directional label is based on summed impact score after grouping. Unavailable groups are counted separately and excluded from return-performance statistics.",
        "",
        "## Aggregated Signal Counts",
        "",
    ]
    if label_counts:
        for label, count in sorted(label_counts.items()):
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No aggregated rows available.")
    lines.append("")

    lines.extend(
        [
            "## Return Bucket Summary",
            "",
            *_markdown_table(
                bucket_summary_df,
                [
                    "return_col",
                    "final_directional_label",
                    "n",
                    "mean_return",
                    "median_return",
                    "std_return",
                    "hit_ratio_positive_return",
                    "hit_ratio_negative_return",
                    "simple_t_stat_vs_zero",
                    "t_stat_note",
                ],
            ),
            "",
            "## Directional Hit Ratio",
            "",
            *_markdown_table(
                directional_hit_ratio_df,
                [
                    "return_col",
                    "final_directional_label",
                    "n",
                    "hit_count",
                    "hit_ratio",
                    "hit_rule",
                ],
            ),
            "",
            "## Statistical Caveats",
            "",
            "- Small samples are not statistically reliable.",
            "- Fixture data is synthetic if fixture mode was used.",
            "- Simple t-statistics are descriptive diagnostics and omit richer controls.",
            "- No conclusion should be drawn without longer out-of-sample testing.",
            "",
            "## Limitations",
            "",
            "- This phase does not run regression diagnostics.",
            "- This phase does not run portfolio optimization or execution logic.",
            "- Repeated news rows are aggregated to reduce duplicated candidate influence, but source quality still requires review.",
            "- Data availability, timestamp quality, and survivorship issues require further validation.",
            "",
            "## Next Steps",
            "",
            "Phase 6C or a later phase should add longer archived samples, baseline controls, regression diagnostics, and in-sample versus out-of-sample checks.",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def save_event_study_summary(markdown: str, output_path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return str(path)
