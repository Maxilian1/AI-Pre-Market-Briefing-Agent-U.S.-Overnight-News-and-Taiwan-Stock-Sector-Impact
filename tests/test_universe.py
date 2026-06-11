from src.universe import BASKETS, TAIWAN_TICKERS, US_TICKERS


def test_us_ticker_universe_contains_phase_1_names():
    expected = {
        "NVDA",
        "AMD",
        "AVGO",
        "MU",
        "INTC",
        "ASML",
        "TSM",
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "QQQ",
        "SOXX",
        "SMH",
    }

    assert expected.issubset(set(US_TICKERS))


def test_taiwan_ticker_universe_contains_phase_1_names():
    expected = {
        "2330.TW",
        "2454.TW",
        "2303.TW",
        "3711.TW",
        "2317.TW",
        "2382.TW",
        "6669.TW",
        "2408.TW",
        "2376.TW",
        "2357.TW",
        "2308.TW",
    }

    assert expected.issubset(set(TAIWAN_TICKERS))


def test_baskets_exist_and_only_reference_known_taiwan_tickers():
    expected_baskets = {
        "Taiwan Semiconductor Basket",
        "Taiwan AI Server Basket",
        "Taiwan Apple Supply Chain Basket",
        "Taiwan Power / Data Center Basket",
    }

    assert expected_baskets == set(BASKETS)

    known_tickers = set(TAIWAN_TICKERS)
    for basket_tickers in BASKETS.values():
        assert basket_tickers
        assert set(basket_tickers).issubset(known_tickers)
