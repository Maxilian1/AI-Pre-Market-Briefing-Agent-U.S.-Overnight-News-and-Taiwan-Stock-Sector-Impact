"""Markdown reports for Phase 6C regression diagnostics."""

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


def render_regression_diagnostics_report(
    panel_df: pd.DataFrame,
    regression_results_df: pd.DataFrame,
    report_label: str | None = None,
) -> str:
    """Render deterministic Phase 6C regression diagnostics."""

    fitted = int((regression_results_df.get("status", pd.Series(dtype=str)) == "fitted").sum()) if not regression_results_df.empty else 0
    insufficient = int((regression_results_df.get("status", pd.Series(dtype=str)) == "insufficient_sample").sum()) if not regression_results_df.empty else 0
    unique_dates = int(panel_df["taiwan_trading_date"].nunique()) if not panel_df.empty and "taiwan_trading_date" in panel_df else 0
    unique_targets = int(panel_df["return_target"].nunique()) if not panel_df.empty and "return_target" in panel_df else 0

    lines: list[str] = [
        "# Regression Diagnostics Summary",
        "",
        f"- Label: {report_label or 'unspecified'}",
        f"- Panel rows: {len(panel_df)}",
        f"- Unique Taiwan trading dates: {unique_dates}",
        f"- Unique return targets: {unique_targets}",
        f"- Fitted models: {fitted}",
        f"- Insufficient-sample models: {insufficient}",
        "- Research disclaimer: This is not investment advice.",
        "",
        "## Input Data",
        "",
        "The input panel is built from Phase 6A return labels after Phase 6B target-day aggregation.",
        "Returns are outcome labels and were not used to generate signals.",
        "",
        "## Research Panel Construction",
        "",
        "The panel keeps available-return target-day rows by default and adds deterministic directional-label dummies.",
        "Each panel row is intended to represent one Taiwan trading date and one return target.",
        "",
        "## Baseline Control Alignment",
        "",
        "U.S. control returns are aligned using the most recent available U.S. trading date strictly before the Taiwan trading date.",
        "Rows are not dropped only because baseline controls are missing.",
        "",
        "## Model Specifications",
        "",
        "- Model A: outcome ~ sum_impact_score",
        "- Model B: outcome ~ sum_impact_score + mean_combined_confidence",
        "- Model C: outcome ~ sum_impact_score + qqq_return + soxx_return + smh_return",
        "- Model D: outcome ~ sum_impact_score + qqq_return + soxx_return + smh_return + nvda_return + tsm_adr_return",
        "- Model E: outcome ~ directional dummies + qqq_return + soxx_return + smh_return",
        "",
        "## Regression Results",
        "",
        *_markdown_table(
            regression_results_df,
            ["dependent_var", "model_name", "n_obs", "r_squared", "adj_r_squared", "status", "notes"],
            limit=40,
        ),
        "",
        "## Insufficient Sample Warnings",
        "",
    ]
    if regression_results_df.empty:
        lines.append("- No regression result rows were generated.")
    else:
        warning_rows = regression_results_df[regression_results_df["status"] != "fitted"]
        if warning_rows.empty:
            lines.append("- No insufficient-sample warnings in this run.")
        else:
            for _, row in warning_rows.iterrows():
                lines.append(f"- {row['dependent_var']} / {row['model_name']}: {row['status']} ({row['notes']})")

    lines.extend(
        [
            "",
            "## Interpretation Caveats",
            "",
            "- Regression diagnostics are not causal proof.",
            "- Small samples are not statistically reliable.",
            "- Fixture or one-day samples cannot support inference.",
            "- Out-of-sample validation is required before interpreting any result as evidence.",
            "- Coefficients are descriptive diagnostics and must be tested on longer archived samples.",
            "",
            "## Next Steps",
            "",
            "Phase 6D or a later phase should add in-sample versus out-of-sample splits, richer baseline controls, robustness checks, and archived multi-day validation.",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def save_regression_diagnostics_report(markdown: str, output_path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return str(path)
