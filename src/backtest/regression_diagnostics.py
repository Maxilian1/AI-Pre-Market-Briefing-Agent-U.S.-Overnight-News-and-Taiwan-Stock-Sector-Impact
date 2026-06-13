"""Regression diagnostics for Phase 6C research panels."""

from __future__ import annotations

import math

import pandas as pd

from src.backtest.event_study import DEFAULT_RETURN_COLUMNS


DEFAULT_DEPENDENT_VARS = list(DEFAULT_RETURN_COLUMNS)
DEFAULT_MODEL_SPECS = [
    {"model_name": "Model A", "x_cols": ["sum_impact_score"]},
    {"model_name": "Model B", "x_cols": ["sum_impact_score", "mean_combined_confidence"]},
    {"model_name": "Model C", "x_cols": ["sum_impact_score", "qqq_return", "soxx_return", "smh_return"]},
    {
        "model_name": "Model D",
        "x_cols": ["sum_impact_score", "qqq_return", "soxx_return", "smh_return", "nvda_return", "tsm_adr_return"],
    },
    {
        "model_name": "Model E",
        "x_cols": ["is_potentially_positive", "is_potentially_negative", "qqq_return", "soxx_return", "smh_return"],
    },
]


def _base_result(y_col: str, x_cols: list[str]) -> dict:
    return {
        "dependent_var": y_col,
        "n_obs": 0,
        "x_cols": "|".join(x_cols),
        "r_squared": math.nan,
        "adj_r_squared": math.nan,
        "status": "",
        "notes": "",
    }


def run_ols_diagnostic(df: pd.DataFrame, y_col: str, x_cols: list[str], min_obs: int = 20) -> dict:
    """Run one OLS diagnostic with robust standard errors when possible."""

    result = _base_result(y_col, x_cols)
    required = [y_col, *x_cols]
    missing_cols = [column for column in required if column not in df.columns]
    if missing_cols:
        result["status"] = "missing_columns"
        result["notes"] = f"missing columns: {','.join(missing_cols)}"
        return result

    model_df = df[required].apply(pd.to_numeric, errors="coerce").dropna()
    n_obs = int(len(model_df))
    result["n_obs"] = n_obs
    parameter_count = len(x_cols) + 1
    if n_obs < min_obs or n_obs <= parameter_count + 2:
        result["status"] = "insufficient_sample"
        result["notes"] = f"n_obs={n_obs}; min_obs={min_obs}; parameters={parameter_count}"
        return result

    try:
        import statsmodels.api as sm
    except ImportError:
        result["status"] = "missing_dependency"
        result["notes"] = "statsmodels is not available."
        return result

    y = model_df[y_col]
    x = sm.add_constant(model_df[x_cols], has_constant="add")
    try:
        fitted = sm.OLS(y, x).fit(cov_type="HC1")
    except Exception as exc:
        result["status"] = "fit_error"
        result["notes"] = str(exc)
        return result

    result["status"] = "fitted"
    result["notes"] = "OLS diagnostic fit with HC1 robust standard errors; not causal proof."
    result["r_squared"] = float(getattr(fitted, "rsquared", math.nan))
    result["adj_r_squared"] = float(getattr(fitted, "rsquared_adj", math.nan))
    for column in x_cols:
        result[f"coef_{column}"] = float(fitted.params.get(column, math.nan))
        result[f"tstat_{column}"] = float(fitted.tvalues.get(column, math.nan))
        result[f"pvalue_{column}"] = float(fitted.pvalues.get(column, math.nan))
    return result


def run_regression_suite(
    panel_df: pd.DataFrame,
    dependent_vars: list[str] | None = None,
    model_specs: list[dict] | None = None,
    min_obs: int = 20,
) -> pd.DataFrame:
    """Run the default Phase 6C regression diagnostic suite."""

    y_cols = dependent_vars or DEFAULT_DEPENDENT_VARS
    specs = model_specs or DEFAULT_MODEL_SPECS
    rows: list[dict] = []
    for y_col in y_cols:
        for spec in specs:
            x_cols = list(spec["x_cols"])
            result = run_ols_diagnostic(panel_df, y_col, x_cols, min_obs=min_obs)
            result["model_name"] = spec["model_name"]
            rows.append(result)
    if not rows:
        return pd.DataFrame()
    columns = ["dependent_var", "model_name", "n_obs", "x_cols", "r_squared", "adj_r_squared", "status", "notes"]
    extras = sorted(set().union(*(set(row.keys()) for row in rows)) - set(columns))
    return pd.DataFrame(rows)[columns + extras]
