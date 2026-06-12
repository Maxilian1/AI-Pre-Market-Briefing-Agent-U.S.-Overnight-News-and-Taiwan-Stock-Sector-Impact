import math

import pandas as pd
import pytest

from src.backtest.event_study import (
    compute_bucket_summary,
    compute_directional_hit_ratio,
    compute_simple_t_stat,
)


def _aggregated_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_directional_label": "potentially_positive",
                "return_data_available": True,
                "open_to_close_return": 0.02,
                "mean_impact_score": 0.2,
                "mean_combined_confidence": 0.7,
            },
            {
                "final_directional_label": "potentially_positive",
                "return_data_available": True,
                "open_to_close_return": -0.01,
                "mean_impact_score": 0.1,
                "mean_combined_confidence": 0.6,
            },
            {
                "final_directional_label": "potentially_negative",
                "return_data_available": True,
                "open_to_close_return": -0.03,
                "mean_impact_score": -0.2,
                "mean_combined_confidence": 0.8,
            },
            {
                "final_directional_label": "potentially_negative",
                "return_data_available": True,
                "open_to_close_return": 0.01,
                "mean_impact_score": -0.1,
                "mean_combined_confidence": 0.5,
            },
            {
                "final_directional_label": "neutral",
                "return_data_available": True,
                "open_to_close_return": 0.005,
                "mean_impact_score": 0.0,
                "mean_combined_confidence": 0.4,
            },
            {
                "final_directional_label": "potentially_positive",
                "return_data_available": True,
                "open_to_close_return": pd.NA,
                "mean_impact_score": 0.3,
                "mean_combined_confidence": 0.4,
            },
            {
                "final_directional_label": "unavailable",
                "return_data_available": False,
                "open_to_close_return": 0.5,
                "mean_impact_score": 0.9,
                "mean_combined_confidence": 0.9,
            },
        ]
    )


def test_positive_and_negative_directional_hit_ratios():
    hit = compute_directional_hit_ratio(_aggregated_rows(), "open_to_close_return")

    positive = hit[hit["final_directional_label"] == "potentially_positive"].iloc[0]
    negative = hit[hit["final_directional_label"] == "potentially_negative"].iloc[0]

    assert positive["hit_count"] == 1
    assert positive["hit_ratio"] == pytest.approx(0.5)
    assert negative["hit_count"] == 1
    assert negative["hit_ratio"] == pytest.approx(0.5)


def test_neutral_directional_hit_ratio_is_not_applicable():
    hit = compute_directional_hit_ratio(_aggregated_rows(), "open_to_close_return")
    neutral = hit[hit["final_directional_label"] == "neutral"].iloc[0]

    assert neutral["n"] == 1
    assert math.isnan(neutral["hit_ratio"])
    assert neutral["hit_rule"] == "not applicable for neutral bucket"


def test_t_stat_returns_nan_when_n_less_than_two():
    result = compute_simple_t_stat([0.01])

    assert result["n"] == 1
    assert math.isnan(result["t_stat"])
    assert "n < 2" in result["note"]


def test_bucket_summary_mean_return_excludes_nan_returns():
    summary = compute_bucket_summary(_aggregated_rows(), "open_to_close_return")
    positive = summary[summary["final_directional_label"] == "potentially_positive"].iloc[0]

    assert positive["n"] == 2
    assert positive["mean_return"] == pytest.approx(0.005)
    assert positive["simple_t_stat_vs_zero"] == pytest.approx(0.33333333333333337)
