"""Research panel construction for Phase 6C regression diagnostics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.backtest.event_study import DEFAULT_RETURN_COLUMNS, aggregate_target_day_signals


PANEL_KEY_COLUMNS = ["taiwan_trading_date", "return_target"]


def _as_paths(paths) -> list:
    if isinstance(paths, (str, Path)):
        return [paths]
    return list(paths)


def _clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _first_non_null(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return pd.NA
    return values.iloc[0]


def _combine_text(series: pd.Series) -> str:
    values = sorted(set(_clean_text(value) for value in series if _clean_text(value)))
    return "; ".join(values)


def load_return_label_files(paths) -> pd.DataFrame:
    """Load one or more Phase 6A return-label CSV files."""

    frames = []
    for path in _as_paths(paths):
        frame = pd.read_csv(path)
        frame["source_return_label_path"] = str(path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _collapse_to_one_row_per_target_day(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    if aggregated_df.empty:
        return aggregated_df.copy()

    rows: list[dict] = []
    for (date_value, target), group in aggregated_df.groupby(PANEL_KEY_COLUMNS, dropna=False, sort=True):
        impact = pd.to_numeric(group["sum_impact_score"], errors="coerce").fillna(0.0)
        available = group["return_data_available"].fillna(False).astype(bool)
        neutral_count = int(pd.to_numeric(group["neutral_count"], errors="coerce").fillna(0).sum())
        sum_impact_score = float(impact.sum())
        if not bool(available.any()):
            final_label = "unavailable"
        elif sum_impact_score > 0:
            final_label = "potentially_positive"
        elif sum_impact_score < 0:
            final_label = "potentially_negative"
        elif neutral_count > 0:
            final_label = "neutral"
        else:
            final_label = "neutral"

        available_group = group[available]
        row = {
            "taiwan_trading_date": _clean_text(date_value),
            "return_target": _clean_text(target),
            "return_target_type": _combine_text(group["return_target_type"]),
            "taiwan_target_type": _combine_text(group["taiwan_target_type"]),
            "taiwan_sector": _combine_text(group["taiwan_sector"]),
            "candidate_count": int(pd.to_numeric(group["candidate_count"], errors="coerce").fillna(0).sum()),
            "positive_count": int(pd.to_numeric(group["positive_count"], errors="coerce").fillna(0).sum()),
            "negative_count": int(pd.to_numeric(group["negative_count"], errors="coerce").fillna(0).sum()),
            "neutral_count": neutral_count,
            "unavailable_count": int(pd.to_numeric(group["unavailable_count"], errors="coerce").fillna(0).sum()),
            "mean_impact_score": float(pd.to_numeric(group["mean_impact_score"], errors="coerce").mean()),
            "sum_impact_score": sum_impact_score,
            "max_abs_impact_score": float(pd.to_numeric(group["max_abs_impact_score"], errors="coerce").max()),
            "mean_combined_confidence": float(pd.to_numeric(group["mean_combined_confidence"], errors="coerce").mean()),
            "final_directional_label": final_label,
            "return_data_available": bool(available.any()),
            "duplicate_key_count": int(max(len(group) - 1, 0)),
            "panel_notes": "duplicate target-day aggregate rows collapsed." if len(group) > 1 else "",
        }
        for return_col in DEFAULT_RETURN_COLUMNS:
            row[return_col] = _first_non_null(available_group[return_col]) if not available_group.empty else pd.NA
        rows.append(row)

    return pd.DataFrame(rows).sort_values(PANEL_KEY_COLUMNS, kind="mergesort").reset_index(drop=True)


def add_directional_dummies(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Add final directional-label dummy variables."""

    panel = panel_df.copy()
    labels = panel.get("final_directional_label", pd.Series(dtype=str)).fillna("").astype(str)
    panel["is_potentially_positive"] = (labels == "potentially_positive").astype(int)
    panel["is_potentially_negative"] = (labels == "potentially_negative").astype(int)
    panel["is_neutral"] = (labels == "neutral").astype(int)
    return panel


def build_target_day_panel(return_labels_df: pd.DataFrame, aggregation_mode: str = "target_day") -> pd.DataFrame:
    """Build one available-return panel row per Taiwan date and return target."""

    if aggregation_mode != "target_day":
        raise ValueError("Phase 6C currently supports aggregation_mode='target_day' only.")
    aggregated = aggregate_target_day_signals(return_labels_df)
    panel = _collapse_to_one_row_per_target_day(aggregated)
    if panel.empty:
        return add_directional_dummies(panel)
    panel = panel[panel["return_data_available"].fillna(False).astype(bool)].copy()
    panel = add_directional_dummies(panel)
    return panel.sort_values(PANEL_KEY_COLUMNS, kind="mergesort").reset_index(drop=True)


def validate_panel(panel_df: pd.DataFrame) -> dict:
    """Return simple QA metadata for a research panel."""

    if panel_df.empty:
        return {
            "row_count": 0,
            "unique_dates": 0,
            "unique_targets": 0,
            "duplicate_key_count": 0,
            "warnings": ["panel is empty"],
        }
    duplicate_key_count = int(panel_df.duplicated(PANEL_KEY_COLUMNS).sum())
    warnings = []
    if duplicate_key_count:
        warnings.append("duplicate taiwan_trading_date/return_target rows detected")
    for return_col in DEFAULT_RETURN_COLUMNS:
        if return_col in panel_df.columns and panel_df[return_col].isna().any():
            warnings.append(f"missing values present in {return_col}")
    return {
        "row_count": int(len(panel_df)),
        "unique_dates": int(panel_df["taiwan_trading_date"].nunique()),
        "unique_targets": int(panel_df["return_target"].nunique()),
        "duplicate_key_count": duplicate_key_count,
        "warnings": warnings,
    }
