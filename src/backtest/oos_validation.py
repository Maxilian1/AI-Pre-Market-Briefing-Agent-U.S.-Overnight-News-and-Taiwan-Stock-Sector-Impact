"""Out-of-sample validation diagnostics for Phase 6D research panels."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.backtest.regression_diagnostics import DEFAULT_DEPENDENT_VARS


DATE_COLUMN = "taiwan_trading_date"

DEFAULT_NEWS_FEATURES = [
    "sum_impact_score",
    "mean_impact_score",
    "max_abs_impact_score",
    "mean_combined_confidence",
    "candidate_count",
    "is_potentially_positive",
    "is_potentially_negative",
]
DEFAULT_BASELINE_CONTROLS = [
    "qqq_return",
    "soxx_return",
    "smh_return",
    "nvda_return",
    "amd_return",
    "tsm_adr_return",
]
DEFAULT_MODEL_SPECS = [
    {
        "model_family": "baseline_only",
        "x_cols": DEFAULT_BASELINE_CONTROLS,
    },
    {
        "model_family": "news_only",
        "x_cols": ["sum_impact_score", "mean_combined_confidence", "candidate_count"],
    },
    {
        "model_family": "news_plus_baseline",
        "x_cols": ["sum_impact_score", "mean_combined_confidence", "candidate_count", *DEFAULT_BASELINE_CONTROLS],
    },
    {
        "model_family": "directional_plus_baseline",
        "x_cols": ["is_potentially_positive", "is_potentially_negative", *DEFAULT_BASELINE_CONTROLS],
    },
]
NEWS_COEFFICIENT_COLUMNS = set(DEFAULT_NEWS_FEATURES)
COMPARISON_PAIRS = [
    ("baseline_only", "news_plus_baseline"),
    ("baseline_only", "directional_plus_baseline"),
]


def _base_result(y_col: str, x_cols: Sequence[str]) -> dict:
    return {
        "dependent_var": y_col,
        "model_family": "",
        "x_cols": "|".join(x_cols),
        "train_n": 0,
        "test_n": 0,
        "train_r_squared": math.nan,
        "test_mse": math.nan,
        "test_mae": math.nan,
        "test_direction_accuracy": math.nan,
        "test_mean_actual_return": math.nan,
        "test_mean_predicted_return": math.nan,
        "status": "",
        "notes": "",
    }


def _sorted_panel(panel_df: pd.DataFrame) -> pd.DataFrame:
    panel = panel_df.copy()
    panel["_oos_sort_date"] = pd.to_datetime(panel[DATE_COLUMN], errors="coerce")
    sort_cols = ["_oos_sort_date"]
    if "return_target" in panel.columns:
        sort_cols.append("return_target")
    return panel.sort_values(sort_cols, kind="mergesort").drop(columns=["_oos_sort_date"]).reset_index(drop=True)


def _unique_sorted_dates(panel_df: pd.DataFrame) -> list[pd.Timestamp]:
    parsed_dates = pd.to_datetime(panel_df[DATE_COLUMN], errors="coerce").dropna()
    return sorted(pd.Timestamp(value).normalize() for value in parsed_dates.unique())


def _date_label(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def validate_oos_inputs(panel_df: pd.DataFrame) -> dict:
    """Validate that an input panel has the minimum shape for OOS splitting."""

    if panel_df.empty:
        return {
            "status": "insufficient_sample",
            "row_count": 0,
            "unique_dates": 0,
            "warnings": ["panel is empty"],
        }
    if DATE_COLUMN not in panel_df.columns:
        return {
            "status": "missing_columns",
            "row_count": int(len(panel_df)),
            "unique_dates": 0,
            "warnings": [f"missing required column: {DATE_COLUMN}"],
        }

    dates = _unique_sorted_dates(panel_df)
    warnings: list[str] = []
    invalid_dates = int(pd.to_datetime(panel_df[DATE_COLUMN], errors="coerce").isna().sum())
    if invalid_dates:
        warnings.append(f"invalid {DATE_COLUMN} rows: {invalid_dates}")
    if "return_target" not in panel_df.columns:
        warnings.append("missing optional return_target column")
    status = "ok" if dates else "insufficient_sample"
    return {
        "status": status,
        "row_count": int(len(panel_df)),
        "unique_dates": int(len(dates)),
        "warnings": warnings,
    }


def chronological_train_test_split(
    panel_df: pd.DataFrame,
    test_fraction: float = 0.3,
    min_train_dates: int = 20,
    min_test_dates: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Split a panel by unique Taiwan trading dates without shuffling rows."""

    validation = validate_oos_inputs(panel_df)
    if validation["status"] != "ok":
        empty = panel_df.iloc[0:0].copy()
        metadata = {
            **validation,
            "split_status": validation["status"],
            "test_fraction": test_fraction,
            "min_train_dates": min_train_dates,
            "min_test_dates": min_test_dates,
            "notes": "; ".join(validation.get("warnings", [])) or "panel cannot be split",
        }
        return empty, empty.copy(), metadata
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1.")

    sorted_panel = _sorted_panel(panel_df)
    dates = _unique_sorted_dates(sorted_panel)
    unique_date_count = len(dates)
    if unique_date_count < min_train_dates + min_test_dates:
        empty = sorted_panel.iloc[0:0].copy()
        metadata = {
            "status": "insufficient_sample",
            "split_status": "insufficient_sample",
            "row_count": int(len(panel_df)),
            "unique_dates": int(unique_date_count),
            "test_fraction": test_fraction,
            "min_train_dates": min_train_dates,
            "min_test_dates": min_test_dates,
            "train_date_count": 0,
            "test_date_count": 0,
            "notes": f"unique_dates={unique_date_count}; required_dates={min_train_dates + min_test_dates}",
        }
        return empty, empty.copy(), metadata

    requested_test_dates = max(min_test_dates, int(math.ceil(unique_date_count * test_fraction)))
    test_date_count = min(requested_test_dates, unique_date_count - min_train_dates)
    train_date_count = unique_date_count - test_date_count
    if train_date_count < min_train_dates or test_date_count < min_test_dates:
        empty = sorted_panel.iloc[0:0].copy()
        metadata = {
            "status": "insufficient_sample",
            "split_status": "insufficient_sample",
            "row_count": int(len(panel_df)),
            "unique_dates": int(unique_date_count),
            "test_fraction": test_fraction,
            "min_train_dates": min_train_dates,
            "min_test_dates": min_test_dates,
            "train_date_count": int(train_date_count),
            "test_date_count": int(test_date_count),
            "notes": "date split cannot satisfy minimum train/test date requirements",
        }
        return empty, empty.copy(), metadata

    train_dates = set(dates[:train_date_count])
    test_dates = set(dates[train_date_count:])
    panel_dates = pd.to_datetime(sorted_panel[DATE_COLUMN], errors="coerce").dt.normalize()
    train_df = sorted_panel[panel_dates.isin(train_dates)].copy().reset_index(drop=True)
    test_df = sorted_panel[panel_dates.isin(test_dates)].copy().reset_index(drop=True)
    metadata = {
        "status": "ok",
        "split_status": "ok",
        "row_count": int(len(panel_df)),
        "unique_dates": int(unique_date_count),
        "test_fraction": test_fraction,
        "min_train_dates": min_train_dates,
        "min_test_dates": min_test_dates,
        "train_date_count": int(train_date_count),
        "test_date_count": int(test_date_count),
        "train_start_date": _date_label(dates[0]),
        "train_end_date": _date_label(dates[train_date_count - 1]),
        "test_start_date": _date_label(dates[train_date_count]),
        "test_end_date": _date_label(dates[-1]),
        "notes": "chronological split by unique Taiwan trading dates; no row shuffle",
    }
    return train_df, test_df, metadata


def fit_train_evaluate_test(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    y_col: str,
    x_cols: Sequence[str],
    min_train_obs: int = 30,
    min_test_obs: int = 10,
) -> dict:
    """Fit OLS on train rows only and evaluate descriptive diagnostics on test rows."""

    result = _base_result(y_col, x_cols)
    required = [y_col, *x_cols]
    missing_cols = [column for column in required if column not in train_df.columns or column not in test_df.columns]
    if missing_cols:
        result["status"] = "missing_columns"
        result["notes"] = f"missing columns: {','.join(sorted(set(missing_cols)))}"
        return result

    train_model = train_df[required].apply(pd.to_numeric, errors="coerce").dropna()
    test_model = test_df[required].apply(pd.to_numeric, errors="coerce").dropna()
    result["train_n"] = int(len(train_model))
    result["test_n"] = int(len(test_model))
    parameter_count = len(x_cols) + 1
    if len(train_model) < min_train_obs or len(test_model) < min_test_obs or len(train_model) <= parameter_count + 2:
        result["status"] = "insufficient_sample"
        result["notes"] = (
            f"train_n={len(train_model)}; test_n={len(test_model)}; "
            f"min_train_obs={min_train_obs}; min_test_obs={min_test_obs}; parameters={parameter_count}"
        )
        return result

    try:
        import statsmodels.api as sm
    except ImportError:
        result["status"] = "missing_dependency"
        result["notes"] = "statsmodels is not available."
        return result

    try:
        x_train = sm.add_constant(train_model[list(x_cols)], has_constant="add")
        y_train = train_model[y_col]
        fitted = sm.OLS(y_train, x_train).fit(cov_type="HC1")
        x_test = sm.add_constant(test_model[list(x_cols)], has_constant="add")
        y_test = test_model[y_col]
        predictions = fitted.predict(x_test)
    except Exception as exc:
        result["status"] = "fit_error"
        result["notes"] = str(exc)
        return result

    errors = predictions.to_numpy(dtype=float) - y_test.to_numpy(dtype=float)
    actual = y_test.to_numpy(dtype=float)
    predicted = predictions.to_numpy(dtype=float)
    result["status"] = "fitted"
    result["notes"] = "OLS fit on train dates only; OOS metrics are descriptive and not causal proof."
    result["train_r_squared"] = float(getattr(fitted, "rsquared", math.nan))
    result["test_mse"] = float(np.mean(errors**2))
    result["test_mae"] = float(np.mean(np.abs(errors)))
    result["test_direction_accuracy"] = float(np.mean(np.sign(predicted) == np.sign(actual)))
    result["test_mean_actual_return"] = float(np.mean(actual))
    result["test_mean_predicted_return"] = float(np.mean(predicted))
    for column in x_cols:
        if column in NEWS_COEFFICIENT_COLUMNS:
            result[f"coef_{column}"] = float(fitted.params.get(column, math.nan))
            result[f"tstat_{column}"] = float(fitted.tvalues.get(column, math.nan))
    return result


def run_oos_validation(
    panel_df: pd.DataFrame,
    dependent_vars: list[str] | None = None,
    model_specs: list[dict] | None = None,
    test_fraction: float = 0.3,
    min_train_dates: int = 20,
    min_test_dates: int = 10,
    min_train_obs: int = 30,
    min_test_obs: int = 10,
) -> pd.DataFrame:
    """Run the default Phase 6D chronological train/test validation suite."""

    y_cols = dependent_vars or DEFAULT_DEPENDENT_VARS
    specs = model_specs or DEFAULT_MODEL_SPECS
    train_df, test_df, split_metadata = chronological_train_test_split(
        panel_df,
        test_fraction=test_fraction,
        min_train_dates=min_train_dates,
        min_test_dates=min_test_dates,
    )
    rows: list[dict] = []
    for y_col in y_cols:
        for spec in specs:
            x_cols = list(spec["x_cols"])
            result = fit_train_evaluate_test(
                train_df,
                test_df,
                y_col,
                x_cols,
                min_train_obs=min_train_obs,
                min_test_obs=min_test_obs,
            )
            result["model_family"] = spec["model_family"]
            result["split_status"] = split_metadata.get("split_status", "")
            result["unique_dates"] = split_metadata.get("unique_dates", 0)
            result["train_date_count"] = split_metadata.get("train_date_count", 0)
            result["test_date_count"] = split_metadata.get("test_date_count", 0)
            result["train_start_date"] = split_metadata.get("train_start_date", "")
            result["train_end_date"] = split_metadata.get("train_end_date", "")
            result["test_start_date"] = split_metadata.get("test_start_date", "")
            result["test_end_date"] = split_metadata.get("test_end_date", "")
            if split_metadata.get("split_status") == "insufficient_sample":
                result["status"] = "insufficient_sample"
                result["notes"] = split_metadata.get("notes", result["notes"])
            rows.append(result)

    if not rows:
        return pd.DataFrame()
    base_columns = [
        "dependent_var",
        "model_family",
        "x_cols",
        "unique_dates",
        "train_date_count",
        "test_date_count",
        "train_start_date",
        "train_end_date",
        "test_start_date",
        "test_end_date",
        "train_n",
        "test_n",
        "train_r_squared",
        "test_mse",
        "test_mae",
        "test_direction_accuracy",
        "test_mean_actual_return",
        "test_mean_predicted_return",
        "split_status",
        "status",
        "notes",
    ]
    extras = sorted(set().union(*(set(row.keys()) for row in rows)) - set(base_columns))
    return pd.DataFrame(rows)[base_columns + extras]


def _single_model_row(oos_results_df: pd.DataFrame, dependent_var: str, model_family: str) -> dict | None:
    matches = oos_results_df[
        (oos_results_df["dependent_var"] == dependent_var)
        & (oos_results_df["model_family"] == model_family)
    ]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()


def compare_model_families(oos_results_df: pd.DataFrame) -> pd.DataFrame:
    """Compare baseline-only OOS diagnostics against news-augmented models."""

    if oos_results_df.empty:
        return pd.DataFrame(
            columns=[
                "dependent_var",
                "baseline_model_family",
                "comparison_model_family",
                "delta_test_mse",
                "delta_test_mae",
                "delta_direction_accuracy",
                "status",
                "interpretation_label",
                "notes",
            ]
        )

    rows: list[dict] = []
    dependent_vars = sorted(oos_results_df["dependent_var"].dropna().unique())
    for y_col in dependent_vars:
        for baseline_family, comparison_family in COMPARISON_PAIRS:
            baseline = _single_model_row(oos_results_df, y_col, baseline_family)
            comparison = _single_model_row(oos_results_df, y_col, comparison_family)
            row = {
                "dependent_var": y_col,
                "baseline_model_family": baseline_family,
                "comparison_model_family": comparison_family,
                "delta_test_mse": math.nan,
                "delta_test_mae": math.nan,
                "delta_direction_accuracy": math.nan,
                "status": "insufficient_sample",
                "interpretation_label": "insufficient_sample",
                "notes": "comparison requires fitted baseline and comparison rows",
            }
            if not baseline or not comparison:
                rows.append(row)
                continue
            if baseline.get("status") != "fitted" or comparison.get("status") != "fitted":
                row["notes"] = f"baseline_status={baseline.get('status')}; comparison_status={comparison.get('status')}"
                rows.append(row)
                continue

            baseline_mse = float(baseline.get("test_mse", math.nan))
            comparison_mse = float(comparison.get("test_mse", math.nan))
            baseline_mae = float(baseline.get("test_mae", math.nan))
            comparison_mae = float(comparison.get("test_mae", math.nan))
            baseline_accuracy = float(baseline.get("test_direction_accuracy", math.nan))
            comparison_accuracy = float(comparison.get("test_direction_accuracy", math.nan))
            row["delta_test_mse"] = baseline_mse - comparison_mse
            row["delta_test_mae"] = baseline_mae - comparison_mae
            row["delta_direction_accuracy"] = comparison_accuracy - baseline_accuracy
            row["status"] = "compared"
            row["notes"] = "positive delta_test_mse means lower test MSE for the comparison model; not statistical proof"
            tolerance = 1e-12
            if row["delta_test_mse"] > tolerance:
                row["interpretation_label"] = "news_improved"
            elif row["delta_test_mse"] < -tolerance:
                row["interpretation_label"] = "baseline_better"
            else:
                row["interpretation_label"] = "tied"
            rows.append(row)
    return pd.DataFrame(rows)
