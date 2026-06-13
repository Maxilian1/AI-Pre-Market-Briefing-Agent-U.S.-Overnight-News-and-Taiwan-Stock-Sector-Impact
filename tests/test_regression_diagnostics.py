import pandas as pd

from src.backtest.regression_diagnostics import run_ols_diagnostic, run_regression_suite
from src.backtest.regression_reporting import render_regression_diagnostics_report
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


def _synthetic_panel() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DATA_DIR / "sample_research_panel_directional.csv")


def test_insufficient_sample_returns_status():
    panel = _synthetic_panel().head(5)

    result = run_ols_diagnostic(panel, "open_to_close_return", ["sum_impact_score"], min_obs=20)

    assert result["status"] == "insufficient_sample"
    assert result["n_obs"] == 5


def test_synthetic_fixture_fits_at_least_one_model():
    panel = _synthetic_panel()

    results = run_regression_suite(panel, min_obs=20)

    assert not results.empty
    assert (results["status"] == "fitted").any()
    assert "coef_sum_impact_score" in results.columns
    assert "tstat_sum_impact_score" in results.columns


def test_nan_rows_are_dropped_per_model():
    panel = _synthetic_panel()
    panel.loc[0, "qqq_return"] = pd.NA

    result = run_ols_diagnostic(
        panel,
        "open_to_close_return",
        ["sum_impact_score", "qqq_return", "soxx_return"],
        min_obs=20,
    )

    assert result["status"] == "fitted"
    assert result["n_obs"] == len(panel) - 1


def test_regression_report_has_caveats_and_no_trading_or_causal_claims():
    panel = _synthetic_panel()
    results = run_regression_suite(panel, min_obs=20)

    report = render_regression_diagnostics_report(panel, results, report_label="synthetic")
    lowered = report.lower()

    assert "not investment advice" in lowered
    assert "not causal proof" in lowered
    assert "small samples are not statistically reliable" in lowered
    assert "fixture or one-day samples cannot support inference" in lowered
    assert "out-of-sample validation is required" in lowered
    assert all(term not in lowered for term in FORBIDDEN_TERMS)
