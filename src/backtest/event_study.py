"""Deterministic Phase 6B event-study diagnostics for return labels."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_RETURN_COLUMNS = [
    "prev_close_to_open_return",
    "open_to_close_return",
    "close_to_close_return",
    "next_close_to_close_return",
]

AGGREGATION_KEYS = [
    "taiwan_trading_date",
    "return_target",
    "return_target_type",
    "taiwan_target_type",
]

FINAL_LABELS = [
    "potentially_positive",
    "potentially_negative",
    "neutral",
    "unavailable",
]


def _as_list(paths) -> list:
    if isinstance(paths, (str, Path)):
        return [paths]
    return list(paths)


def _clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_bool_series(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    if series.dtype == bool:
        return series.fillna(False)
    normalized = series.fillna(False).astype(str).str.strip().str.lower()
    return normalized.isin({"true", "1", "yes", "y"})


def _first_non_null(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return pd.NA
    return values.iloc[0]


def _directional_label(sum_impact_score: float, neutral_count: int, group_available: bool) -> str:
    if not group_available:
        return "unavailable"
    if sum_impact_score > 0:
        return "potentially_positive"
    if sum_impact_score < 0:
        return "potentially_negative"
    if neutral_count > 0:
        return "neutral"
    return "neutral"


def load_return_labels(paths) -> pd.DataFrame:
    """Load one or more Phase 6A return-label CSV files."""

    frames = []
    for path in _as_list(paths):
        frame = pd.read_csv(path)
        frame["source_return_label_path"] = str(path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def aggregate_target_day_signals(return_labels_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate news-candidate return rows to target/day observations."""

    if return_labels_df.empty:
        return pd.DataFrame(
            columns=[
                *AGGREGATION_KEYS,
                "taiwan_sector",
                "candidate_count",
                "positive_count",
                "negative_count",
                "neutral_count",
                "unavailable_count",
                "mean_impact_score",
                "sum_impact_score",
                "max_abs_impact_score",
                "mean_combined_confidence",
                "final_directional_label",
                *DEFAULT_RETURN_COLUMNS,
                "return_data_available",
            ]
        )

    working = return_labels_df.copy()
    for column in AGGREGATION_KEYS:
        if column not in working.columns:
            working[column] = ""
        working[column] = working[column].map(_clean_text)
    if "taiwan_sector" not in working.columns:
        working["taiwan_sector"] = ""
    working["taiwan_sector"] = working["taiwan_sector"].map(_clean_text)
    for column in ["impact_score", "combined_confidence", *DEFAULT_RETURN_COLUMNS]:
        if column not in working.columns:
            working[column] = pd.NA
        working[column] = pd.to_numeric(working[column], errors="coerce")
    if "directional_impact_label" not in working.columns:
        working["directional_impact_label"] = ""
    if "return_data_available" not in working.columns:
        working["return_data_available"] = False
    working["_return_available_bool"] = _to_bool_series(working["return_data_available"])

    rows: list[dict] = []
    grouped = working.groupby(AGGREGATION_KEYS, dropna=False, sort=True)
    for group_key, group in grouped:
        labels = group["directional_impact_label"].fillna("").astype(str)
        impact = group["impact_score"].fillna(0.0)
        confidence = group["combined_confidence"]
        available = group["_return_available_bool"]
        group_available = bool(available.any())
        neutral_count = int((labels == "neutral").sum())
        sum_impact_score = float(impact.sum())

        row = {
            key: value for key, value in zip(AGGREGATION_KEYS, group_key)
        }
        row.update(
            {
                "taiwan_sector": "; ".join(
                    sorted(set(value for value in group["taiwan_sector"].dropna().astype(str) if value.strip()))
                ),
                "candidate_count": int(len(group)),
                "positive_count": int((labels == "potentially_positive").sum()),
                "negative_count": int((labels == "potentially_negative").sum()),
                "neutral_count": neutral_count,
                "unavailable_count": int((~available).sum()),
                "mean_impact_score": float(impact.mean()) if len(impact) else math.nan,
                "sum_impact_score": sum_impact_score,
                "max_abs_impact_score": float(impact.abs().max()) if len(impact) else math.nan,
                "mean_combined_confidence": float(confidence.mean(skipna=True)) if confidence.notna().any() else math.nan,
                "final_directional_label": _directional_label(sum_impact_score, neutral_count, group_available),
                "return_data_available": group_available,
            }
        )
        available_group = group[group["_return_available_bool"]]
        for return_col in DEFAULT_RETURN_COLUMNS:
            row[return_col] = _first_non_null(available_group[return_col]) if not available_group.empty else pd.NA
        rows.append(row)

    return pd.DataFrame(rows).sort_values(AGGREGATION_KEYS, kind="mergesort").reset_index(drop=True)


def compute_simple_t_stat(values) -> dict:
    """Compute a simple one-sample t-statistic versus zero."""

    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    n = int(len(series))
    if n < 2:
        return {"n": n, "t_stat": math.nan, "note": "n < 2; t-statistic not computed."}
    std = float(series.std(ddof=1))
    if std == 0 or math.isnan(std):
        return {"n": n, "t_stat": math.nan, "note": "std == 0; t-statistic not computed."}
    mean = float(series.mean())
    return {"n": n, "t_stat": mean / (std / math.sqrt(n)), "note": ""}


def _available_rows(aggregated_df: pd.DataFrame, return_col: str) -> pd.DataFrame:
    if aggregated_df.empty:
        return aggregated_df.copy()
    return aggregated_df[
        aggregated_df["return_data_available"].fillna(False).astype(bool)
        & pd.to_numeric(aggregated_df[return_col], errors="coerce").notna()
        & (aggregated_df["final_directional_label"] != "unavailable")
    ].copy()


def compute_bucket_summary(aggregated_df: pd.DataFrame, return_col: str) -> pd.DataFrame:
    """Compute return statistics by final directional label."""

    data = _available_rows(aggregated_df, return_col)
    rows: list[dict] = []
    for label in ["potentially_positive", "potentially_negative", "neutral"]:
        group = data[data["final_directional_label"] == label]
        returns = pd.to_numeric(group[return_col], errors="coerce").dropna()
        t_stat = compute_simple_t_stat(returns)
        rows.append(
            {
                "return_col": return_col,
                "final_directional_label": label,
                "n": int(len(returns)),
                "mean_return": float(returns.mean()) if len(returns) else math.nan,
                "median_return": float(returns.median()) if len(returns) else math.nan,
                "std_return": float(returns.std(ddof=1)) if len(returns) > 1 else math.nan,
                "min_return": float(returns.min()) if len(returns) else math.nan,
                "max_return": float(returns.max()) if len(returns) else math.nan,
                "hit_ratio_positive_return": float((returns > 0).mean()) if len(returns) else math.nan,
                "hit_ratio_negative_return": float((returns < 0).mean()) if len(returns) else math.nan,
                "mean_impact_score": float(group["mean_impact_score"].mean()) if not group.empty else math.nan,
                "mean_combined_confidence": float(group["mean_combined_confidence"].mean()) if not group.empty else math.nan,
                "simple_t_stat_vs_zero": t_stat["t_stat"],
                "t_stat_note": t_stat["note"],
            }
        )
    return pd.DataFrame(rows)


def compute_directional_hit_ratio(aggregated_df: pd.DataFrame, return_col: str) -> pd.DataFrame:
    """Compute directional hit ratios for positive/negative buckets."""

    data = _available_rows(aggregated_df, return_col)
    rows: list[dict] = []
    specs = [
        ("potentially_positive", lambda values: values > 0, "return > 0"),
        ("potentially_negative", lambda values: values < 0, "return < 0"),
        ("neutral", None, "not applicable for neutral bucket"),
    ]
    for label, predicate, rule in specs:
        group = data[data["final_directional_label"] == label]
        returns = pd.to_numeric(group[return_col], errors="coerce").dropna()
        if predicate is None or len(returns) == 0:
            hit_ratio = math.nan
            hit_count = 0
        else:
            hits = predicate(returns)
            hit_count = int(hits.sum())
            hit_ratio = float(hits.mean())
        rows.append(
            {
                "return_col": return_col,
                "final_directional_label": label,
                "n": int(len(returns)),
                "hit_count": hit_count,
                "hit_ratio": hit_ratio,
                "hit_rule": rule,
            }
        )
    return pd.DataFrame(rows)


def run_event_study(
    return_labels_df: pd.DataFrame,
    return_cols: Iterable[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Run Phase 6B event-study diagnostics for return labels."""

    selected_return_cols = list(return_cols) if return_cols is not None else list(DEFAULT_RETURN_COLUMNS)
    aggregated = aggregate_target_day_signals(return_labels_df)
    bucket_summaries = [
        compute_bucket_summary(aggregated, return_col)
        for return_col in selected_return_cols
    ]
    hit_ratios = [
        compute_directional_hit_ratio(aggregated, return_col)
        for return_col in selected_return_cols
    ]
    return {
        "aggregated": aggregated,
        "bucket_summary": pd.concat(bucket_summaries, ignore_index=True) if bucket_summaries else pd.DataFrame(),
        "directional_hit_ratio": pd.concat(hit_ratios, ignore_index=True) if hit_ratios else pd.DataFrame(),
    }
