import pytest

import pandas as pd

from src.config import FIXTURES_DATA_DIR
from src.market_data.returns import compute_single_ticker_returns
from src.market_data.yfinance_loader import load_price_data, normalize_yfinance_output


def test_fixture_price_data_loads():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")

    assert not prices.empty
    assert {"date", "ticker", "open", "high", "low", "close", "adj_close", "volume"}.issubset(prices.columns)
    assert "2330.TW" in set(prices["ticker"])


def test_ticker_return_calculations_are_correct_for_fixture_case():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")
    returns = compute_single_ticker_returns(prices)
    row = returns[(returns["return_target"] == "2330.TW") & (returns["date"] == "2026-01-15")].iloc[0]

    assert row["open_price"] == 1006
    assert row["close_price"] == 1007
    assert row["previous_close_price"] == 1005
    assert row["next_close_price"] == 1009
    assert row["prev_close_to_open_return"] == pytest.approx(1006 / 1005 - 1)
    assert row["open_to_close_return"] == pytest.approx(1007 / 1006 - 1)
    assert row["close_to_close_return"] == pytest.approx(1007 / 1005 - 1)
    assert row["next_close_to_close_return"] == pytest.approx(1009 / 1007 - 1)
    assert bool(row["return_data_available"]) is True


def test_previous_and_next_close_align_by_trading_rows_not_calendar_days():
    prices = pd.DataFrame(
        [
            {"date": "2026-01-16", "ticker": "TEST.TW", "open": 100, "high": 102, "low": 99, "close": 101},
            {"date": "2026-01-20", "ticker": "TEST.TW", "open": 102, "high": 104, "low": 101, "close": 103},
        ]
    )

    returns = compute_single_ticker_returns(prices)
    first = returns[returns["date"] == "2026-01-16"].iloc[0]
    second = returns[returns["date"] == "2026-01-20"].iloc[0]

    assert first["next_close_price"] == 103
    assert second["previous_close_price"] == 101


def test_normalize_yfinance_output_handles_multiindex_columns():
    columns = pd.MultiIndex.from_product(
        [["2330.TW"], ["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    )
    raw = pd.DataFrame(
        [[100, 103, 99, 101, 101, 1000]],
        index=pd.to_datetime(["2026-01-15"]),
        columns=columns,
    )

    normalized = normalize_yfinance_output(raw)

    assert list(normalized.columns) == ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    assert normalized.iloc[0]["date"] == "2026-01-15"
    assert normalized.iloc[0]["ticker"] == "2330.TW"
    assert normalized.iloc[0]["close"] == 101
