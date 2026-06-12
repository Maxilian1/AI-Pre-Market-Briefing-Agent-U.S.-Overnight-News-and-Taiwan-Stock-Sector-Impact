import pandas as pd
import pytest

from src.backtest.event_study import aggregate_target_day_signals, compute_bucket_summary


def _row(
    target: str = "2330.TW",
    label: str = "potentially_positive",
    impact: float = 0.2,
    available: bool = True,
    sector: str = "Semiconductor Foundry",
) -> dict:
    return {
        "taiwan_trading_date": "2026-01-15",
        "return_target": target,
        "return_target_type": "ticker",
        "taiwan_target_type": "ticker",
        "taiwan_sector": sector,
        "directional_impact_label": label,
        "impact_score": impact,
        "combined_confidence": 0.5,
        "prev_close_to_open_return": 0.01,
        "open_to_close_return": 0.02,
        "close_to_close_return": 0.03,
        "next_close_to_close_return": 0.04,
        "return_data_available": available,
    }


def test_duplicate_same_date_same_ticker_rows_aggregate_into_one_row():
    labels = pd.DataFrame([_row(impact=0.2), _row(impact=0.1)])

    aggregated = aggregate_target_day_signals(labels)
    row = aggregated.iloc[0]

    assert len(aggregated) == 1
    assert row["candidate_count"] == 2
    assert row["positive_count"] == 2
    assert row["sum_impact_score"] == pytest.approx(0.3)
    assert row["final_directional_label"] == "potentially_positive"


def test_same_date_same_ticker_with_different_sectors_aggregates_once():
    labels = pd.DataFrame(
        [
            _row(target="2382.TW", sector="AI Server and ODM", impact=0.1),
            _row(target="2382.TW", sector="Apple Supply Chain", impact=0.0, label="neutral"),
        ]
    )

    aggregated = aggregate_target_day_signals(labels)
    row = aggregated.iloc[0]

    assert len(aggregated) == 1
    assert row["return_target"] == "2382.TW"
    assert row["candidate_count"] == 2
    assert "AI Server and ODM" in row["taiwan_sector"]
    assert "Apple Supply Chain" in row["taiwan_sector"]


def test_sum_impact_score_determines_final_directional_label():
    labels = pd.DataFrame([_row(label="potentially_negative", impact=-0.2), _row(label="neutral", impact=0.05)])

    aggregated = aggregate_target_day_signals(labels)

    assert aggregated.iloc[0]["sum_impact_score"] == pytest.approx(-0.15)
    assert aggregated.iloc[0]["final_directional_label"] == "potentially_negative"


def test_neutral_rows_remain_neutral_when_summed_impact_is_zero():
    labels = pd.DataFrame([_row(label="neutral", impact=0.0), _row(label="neutral", impact=0.0)])

    aggregated = aggregate_target_day_signals(labels)

    assert aggregated.iloc[0]["neutral_count"] == 2
    assert aggregated.iloc[0]["final_directional_label"] == "neutral"


def test_return_values_are_preserved_after_aggregation():
    labels = pd.DataFrame([_row(), _row()])

    aggregated = aggregate_target_day_signals(labels)
    row = aggregated.iloc[0]

    assert row["prev_close_to_open_return"] == 0.01
    assert row["open_to_close_return"] == 0.02
    assert row["close_to_close_return"] == 0.03
    assert row["next_close_to_close_return"] == 0.04


def test_unavailable_rows_are_counted_and_excluded_from_stats():
    labels = pd.DataFrame([_row(target="unmapped", label="unmapped", impact=0.0, available=False, sector="")])

    aggregated = aggregate_target_day_signals(labels)
    summary = compute_bucket_summary(aggregated, "open_to_close_return")

    assert aggregated.iloc[0]["final_directional_label"] == "unavailable"
    assert aggregated.iloc[0]["unavailable_count"] == 1
    assert summary["n"].sum() == 0
