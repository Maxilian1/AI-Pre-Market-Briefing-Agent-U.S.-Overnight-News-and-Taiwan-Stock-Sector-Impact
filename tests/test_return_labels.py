import pandas as pd

from src.config import FIXTURES_DATA_DIR
from src.market_data.return_labels import build_return_labels
from src.market_data.returns import (
    compute_equal_weight_basket_returns,
    compute_single_ticker_returns,
)
from src.market_data.yfinance_loader import load_price_data


def _candidate(
    target_type: str,
    ticker: str,
    target: str,
    direction: str = "neutral",
    impact_score: float = 0.0,
) -> dict:
    return {
        "taiwan_trading_date": "2026-01-15",
        "taiwan_target": target,
        "taiwan_target_type": target_type,
        "taiwan_ticker": ticker,
        "taiwan_company": "Fixture Company",
        "taiwan_sector": "Fixture Sector",
        "directional_impact_label": direction,
        "impact_score": impact_score,
        "combined_confidence": 0.5,
    }


def _returns_frames():
    prices = load_price_data(FIXTURES_DATA_DIR / "sample_prices_daily.csv")
    ticker_returns = compute_single_ticker_returns(prices)
    basket_returns = compute_equal_weight_basket_returns(
        ticker_returns,
        "BASKET:TW_SEMICONDUCTOR",
        ["2330.TW", "2454.TW", "2303.TW", "3711.TW", "2408.TW"],
    )
    return ticker_returns, basket_returns


def test_ticker_impact_candidate_joins_same_date_returns():
    ticker_returns, basket_returns = _returns_frames()
    candidates = pd.DataFrame([_candidate("ticker", "2330.TW", "2330.TW TSMC")])

    labels = build_return_labels(candidates, ticker_returns, basket_returns)
    row = labels.iloc[0]

    assert len(labels) == 1
    assert row["return_target"] == "2330.TW"
    assert row["return_target_type"] == "ticker"
    assert bool(row["return_data_available"]) is True
    assert row["open_price"] == 1006


def test_basket_impact_candidate_joins_basket_returns():
    ticker_returns, basket_returns = _returns_frames()
    candidates = pd.DataFrame(
        [_candidate("basket", "BASKET:TW_SEMICONDUCTOR", "BASKET:TW_SEMICONDUCTOR")]
    )

    labels = build_return_labels(candidates, ticker_returns, basket_returns)
    row = labels.iloc[0]

    assert row["return_target"] == "BASKET:TW_SEMICONDUCTOR"
    assert row["return_target_type"] == "basket"
    assert bool(row["return_data_available"]) is True
    assert pd.isna(row["open_price"])
    assert pd.notna(row["open_to_close_return"])


def test_human_readable_basket_name_maps_to_basket_marker():
    ticker_returns, basket_returns = _returns_frames()
    candidates = pd.DataFrame(
        [_candidate("basket", "", "Taiwan Semiconductor Basket")]
    )

    labels = build_return_labels(candidates, ticker_returns, basket_returns)
    row = labels.iloc[0]

    assert row["return_target"] == "BASKET:TW_SEMICONDUCTOR"
    assert bool(row["return_data_available"]) is True


def test_proxy_and_unmapped_rows_are_retained_but_unavailable():
    ticker_returns, basket_returns = _returns_frames()
    candidates = pd.DataFrame(
        [
            _candidate("proxy", "PROXY:QQQ", "Nasdaq / QQQ Control"),
            _candidate("unmapped", "", "unmapped"),
        ]
    )

    labels = build_return_labels(candidates, ticker_returns, basket_returns)

    assert len(labels) == 2
    assert labels["return_data_available"].tolist() == [False, False]
    assert set(labels["return_target_type"]) == {"proxy", "unmapped"}


def test_no_rows_are_dropped_and_signal_metadata_is_preserved():
    ticker_returns, basket_returns = _returns_frames()
    candidates = pd.DataFrame(
        [
            _candidate("ticker", "2330.TW", "2330.TW TSMC", direction="potentially_positive", impact_score=0.2),
            _candidate("ticker", "9999.TW", "9999.TW Missing", direction="potentially_negative", impact_score=-0.3),
            _candidate("unmapped", "", "unmapped", direction="unmapped"),
        ]
    )

    labels = build_return_labels(candidates, ticker_returns, basket_returns)

    assert len(labels) == len(candidates)
    assert labels.iloc[0]["directional_impact_label"] == "potentially_positive"
    assert labels.iloc[0]["impact_score"] == 0.2
    assert bool(labels.iloc[0]["return_data_available"]) is True
    assert bool(labels.iloc[1]["return_data_available"]) is False
    assert "missing price return labels" in labels.iloc[1]["return_data_notes"]
    assert bool(labels.iloc[2]["return_data_available"]) is False
