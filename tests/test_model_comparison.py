import pandas as pd

from src.backtest.oos_validation import compare_model_families, run_oos_validation
from src.config import FIXTURES_DATA_DIR


def _synthetic_oos_panel() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DATA_DIR / "sample_research_panel_oos.csv")


def test_baseline_vs_news_model_comparison_produces_delta_metrics():
    panel = _synthetic_oos_panel()
    results = run_oos_validation(panel)

    comparison = compare_model_families(results)

    assert not comparison.empty
    assert {"delta_test_mse", "delta_test_mae", "delta_direction_accuracy"}.issubset(comparison.columns)
    assert {"news_plus_baseline", "directional_plus_baseline"}.issubset(set(comparison["comparison_model_family"]))


def test_model_comparison_interpretation_label_is_bounded():
    panel = _synthetic_oos_panel()
    results = run_oos_validation(panel)

    comparison = compare_model_families(results)

    allowed = {"news_improved", "baseline_better", "tied", "insufficient_sample"}
    assert set(comparison["interpretation_label"]).issubset(allowed)
