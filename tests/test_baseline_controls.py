import pytest

import pandas as pd

from src.backtest.baseline_controls import (
    align_controls_to_taiwan_dates,
    compute_control_returns,
)
from src.config import FIXTURES_DATA_DIR
from src.market_data.yfinance_loader import load_price_data


def test_us_control_returns_are_computed_correctly():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")

    controls = compute_control_returns(prices)
    row = controls[controls["us_trading_date"] == "2026-01-14"].iloc[0]

    assert row["qqq_return"] == pytest.approx(505 / 503 - 1)
    assert row["soxx_return"] == pytest.approx(255 / 253 - 1)


def test_taiwan_date_aligns_to_previous_available_us_trading_date():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")
    controls = compute_control_returns(prices)
    panel = pd.DataFrame(
        [
            {
                "taiwan_trading_date": "2026-01-15",
                "return_target": "2330.TW",
            }
        ]
    )

    aligned = align_controls_to_taiwan_dates(panel, controls)

    assert aligned.iloc[0]["us_control_date"] == "2026-01-14"
    assert aligned.iloc[0]["qqq_return"] == pytest.approx(505 / 503 - 1)


def test_missing_control_ticker_creates_nan_column_and_warning():
    price_df = pd.DataFrame(
        [
            {"date": "2026-01-14", "ticker": "QQQ", "open": 100, "high": 101, "low": 99, "close": 100},
            {"date": "2026-01-15", "ticker": "QQQ", "open": 101, "high": 102, "low": 100, "close": 102},
        ]
    )

    controls = compute_control_returns(price_df)

    assert "soxx_return" in controls.columns
    assert controls["soxx_return"].isna().all()
    assert any("SOXX" in warning for warning in controls.attrs["warnings"])


def test_no_calendar_day_assumption_for_control_alignment():
    controls = pd.DataFrame(
        [
            {"us_trading_date": "2026-01-10", "qqq_return": 0.01},
            {"us_trading_date": "2026-01-14", "qqq_return": 0.02},
        ]
    )
    panel = pd.DataFrame([{"taiwan_trading_date": "2026-01-16", "return_target": "2330.TW"}])

    aligned = align_controls_to_taiwan_dates(panel, controls)

    assert aligned.iloc[0]["us_control_date"] == "2026-01-14"
    assert aligned.iloc[0]["qqq_return"] == 0.02
