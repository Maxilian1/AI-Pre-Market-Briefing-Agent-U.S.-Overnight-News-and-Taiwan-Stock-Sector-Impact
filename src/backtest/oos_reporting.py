"""Markdown reports for Phase 6D out-of-sample validation."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


def _fmt(value, digits: int = 6) -> str:
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


def render_oos_validation_report(
    panel_df: pd.DataFrame,
    oos_results_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    report_label: str | None = None,
    data_mode: str = "unknown",
) -> str:
    """Render a deterministic Phase 6D OOS validation report."""

    fitted = int((oos_results_df.get("status", pd.Series(dtype=str)) == "fitted").sum()) if not oos_results_df.empty else 0
    insufficient = (
        int((oos_results_df.get("status", pd.Series(dtype=str)) == "insufficient_sample").sum())
        if not oos_results_df.empty
        else 0
    )
    unique_dates = int(panel_df["taiwan_trading_date"].nunique()) if not panel_df.empty and "taiwan_trading_date" in panel_df else 0
    unique_targets = int(panel_df["return_target"].nunique()) if not panel_df.empty and "return_target" in panel_df else 0

    lines: list[str] = [
        "# Out-of-Sample Validation Summary",
        "",
        f"- Label: {report_label or 'unspecified'}",
        f"- Data mode: {data_mode}",
        f"- Panel rows: {len(panel_df)}",
        f"- Unique Taiwan trading dates: {unique_dates}",
        f"- Unique return targets: {unique_targets}",
        f"- Fitted validations: {fitted}",
        f"- Insufficient-sample validations: {insufficient}",
        "- Research disclaimer: This is not investment advice.",
        "",
        "## Input Data",
        "",
        "The input is a Phase 6C research panel with one row per Taiwan trading date and return target.",
        "Return columns are outcome labels and are not used to construct news signals.",
        "",
        "## Chronological Split Method",
        "",
        "Rows are sorted by `taiwan_trading_date` and split by unique dates.",
        "The training period uses only dates strictly before the test period.",
        "No random shuffle split is used.",
        "",
        "## Model Families",
        "",
        "- baseline_only: outcome ~ QQQ + SOXX + SMH + NVDA + AMD + TSM ADR controls",
        "- news_only: outcome ~ sum impact score + mean combined confidence + candidate count",
        "- news_plus_baseline: outcome ~ news features + baseline controls",
        "- directional_plus_baseline: outcome ~ directional dummies + baseline controls",
        "",
        "## Baseline vs News Model Comparison",
        "",
        *_markdown_table(
            comparison_df,
            [
                "dependent_var",
                "baseline_model_family",
                "comparison_model_family",
                "delta_test_mse",
                "delta_test_mae",
                "delta_direction_accuracy",
                "status",
                "interpretation_label",
            ],
            limit=40,
        ),
        "",
        "## Validation Results",
        "",
        *_markdown_table(
            oos_results_df,
            [
                "dependent_var",
                "model_family",
                "train_n",
                "test_n",
                "train_r_squared",
                "test_mse",
                "test_mae",
                "test_direction_accuracy",
                "status",
            ],
            limit=80,
        ),
        "",
        "## Insufficient Sample Warnings",
        "",
    ]
    if oos_results_df.empty:
        lines.append("- No OOS validation rows were generated.")
    else:
        warning_rows = oos_results_df[oos_results_df["status"] != "fitted"]
        if warning_rows.empty:
            lines.append("- No insufficient-sample warnings in this run.")
        else:
            for _, row in warning_rows.iterrows():
                lines.append(f"- {row['dependent_var']} / {row['model_family']}: {row['status']} ({row['notes']})")

    lines.extend(
        [
            "",
            "## Interpretation Caveats",
            "",
            "- This is not investment advice.",
            "- Out-of-sample diagnostics are not causal proof.",
            "- Small samples are not reliable.",
            "- Fixture/synthetic data cannot support market conclusions.",
            "- Interpretation labels are mechanical metric comparisons, not market conclusions.",
            "- News factor usefulness requires longer live archive or historical news dataset.",
            "- Look-ahead bias controls depend on correct timestamps.",
            "- OOS metric differences alone do not establish statistical significance.",
            "",
            "## Next Steps",
            "",
            "Extend the archived research panel across many Taiwan trading dates, audit timestamps and data revisions, and rerun the same chronological protocol on live or historical data.",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def save_oos_validation_report(markdown: str, output_path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return str(path)
