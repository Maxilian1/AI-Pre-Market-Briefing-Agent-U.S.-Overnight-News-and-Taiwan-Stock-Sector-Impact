import pandas as pd

from src.backtest.oos_reporting import render_oos_validation_report
from src.backtest.oos_validation import (
    DEFAULT_BASELINE_CONTROLS,
    chronological_train_test_split,
    compare_model_families,
    fit_train_evaluate_test,
    run_oos_validation,
)
from src.config import FIXTURES_DATA_DIR


FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "recommendation",
    "recommendations",
    "will rise",
    "will fall",
    "guaranteed",
    "target price",
    "must trade",
]


def _synthetic_oos_panel() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DATA_DIR / "sample_research_panel_oos.csv")


def test_synthetic_oos_fixture_fits_at_least_one_model():
    panel = _synthetic_oos_panel()

    results = run_oos_validation(panel)

    assert not results.empty
    assert (results["status"] == "fitted").any()
    assert "test_mse" in results.columns
    assert "test_mae" in results.columns
    assert "test_direction_accuracy" in results.columns


def test_nan_rows_are_dropped_per_model():
    panel = _synthetic_oos_panel()
    train_df, test_df, _ = chronological_train_test_split(panel)
    train_df.loc[0, "qqq_return"] = pd.NA

    result = fit_train_evaluate_test(
        train_df,
        test_df,
        "open_to_close_return",
        DEFAULT_BASELINE_CONTROLS,
        min_train_obs=30,
        min_test_obs=10,
    )

    assert result["status"] == "fitted"
    assert result["train_n"] == len(train_df) - 1


def test_insufficient_train_or_test_obs_handled_safely():
    panel = _synthetic_oos_panel().head(12)

    results = run_oos_validation(panel)

    assert not results.empty
    assert set(results["status"]) == {"insufficient_sample"}


def test_oos_report_has_caveats_and_no_forbidden_trading_terms():
    panel = _synthetic_oos_panel()
    results = run_oos_validation(panel)
    comparison = compare_model_families(results)

    report = render_oos_validation_report(panel, results, comparison, report_label="synthetic", data_mode="synthetic")
    lowered = report.lower()

    assert "this is not investment advice" in lowered
    assert "out-of-sample diagnostics are not causal proof" in lowered
    assert "fixture/synthetic data cannot support market conclusions" in lowered
    assert all(term not in lowered for term in FORBIDDEN_TERMS)
