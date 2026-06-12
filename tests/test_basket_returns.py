import pytest

import pandas as pd

from src.config import FIXTURES_DATA_DIR
from src.market_data.return_labels import basket_marker_to_constituents
from src.market_data.returns import (
    compute_equal_weight_basket_returns,
    compute_single_ticker_returns,
)
from src.market_data.yfinance_loader import load_price_data


def test_equal_weight_basket_returns_are_computed_from_constituents():
    prices = pd.DataFrame(
        [
            {"date": "2026-01-14", "ticker": "AAA", "open": 100, "high": 103, "low": 99, "close": 101},
            {"date": "2026-01-15", "ticker": "AAA", "open": 102, "high": 104, "low": 101, "close": 104},
            {"date": "2026-01-16", "ticker": "AAA", "open": 105, "high": 107, "low": 104, "close": 106},
            {"date": "2026-01-14", "ticker": "BBB", "open": 200, "high": 203, "low": 199, "close": 202},
            {"date": "2026-01-15", "ticker": "BBB", "open": 204, "high": 206, "low": 203, "close": 206},
            {"date": "2026-01-16", "ticker": "BBB", "open": 208, "high": 210, "low": 207, "close": 210},
        ]
    )
    ticker_returns = compute_single_ticker_returns(prices)

    basket = compute_equal_weight_basket_returns(ticker_returns, "BASKET:TEST", ["AAA", "BBB"])
    row = basket[basket["date"] == "2026-01-15"].iloc[0]
    aaa = ticker_returns[(ticker_returns["return_target"] == "AAA") & (ticker_returns["date"] == "2026-01-15")].iloc[0]
    bbb = ticker_returns[(ticker_returns["return_target"] == "BBB") & (ticker_returns["date"] == "2026-01-15")].iloc[0]

    expected = (aaa["open_to_close_return"] + bbb["open_to_close_return"]) / 2
    assert row["return_target"] == "BASKET:TEST"
    assert row["return_target_type"] == "basket"
    assert row["open_to_close_return"] == pytest.approx(expected)
    assert bool(row["return_data_available"]) is True


def test_basket_returns_note_missing_constituents():
    prices = pd.DataFrame(
        [
            {"date": "2026-01-14", "ticker": "AAA", "open": 100, "high": 103, "low": 99, "close": 101},
            {"date": "2026-01-15", "ticker": "AAA", "open": 102, "high": 104, "low": 101, "close": 104},
            {"date": "2026-01-16", "ticker": "AAA", "open": 105, "high": 107, "low": 104, "close": 106},
        ]
    )
    ticker_returns = compute_single_ticker_returns(prices)

    basket = compute_equal_weight_basket_returns(ticker_returns, "BASKET:TEST", ["AAA", "MISSING"])
    row = basket[basket["date"] == "2026-01-15"].iloc[0]

    assert row["open_to_close_return"] == pytest.approx(
        ticker_returns[(ticker_returns["return_target"] == "AAA") & (ticker_returns["date"] == "2026-01-15")].iloc[0][
            "open_to_close_return"
        ]
    )
    assert "missing_constituents=MISSING" in row["return_data_notes"]


def test_tw_semiconductor_basket_computes_from_fixture_constituents():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")
    ticker_returns = compute_single_ticker_returns(prices)
    constituents = basket_marker_to_constituents()["BASKET:TW_SEMICONDUCTOR"]

    basket = compute_equal_weight_basket_returns(ticker_returns, "BASKET:TW_SEMICONDUCTOR", constituents)

    assert not basket.empty
    assert "2026-01-15" in set(basket["date"])
    assert bool(basket[basket["date"] == "2026-01-15"].iloc[0]["return_data_available"]) is True
