import pandas as pd

from src.mapping.ticker_mapper import (
    load_mapping_table,
    map_signal_row,
    map_signals_dataframe,
    parse_pipe_or_json_list,
)


FORBIDDEN_REASONING_TERMS = ["buy", "sell", "guaranteed", "will rise", "will fall"]


def _signal(
    us_tickers: str,
    sentiment_label: str = "positive",
    sentiment_score: float = 0.7,
    sector: str = "AI Infrastructure",
    theme: str = "AI chip demand",
    relevance_label: str = "high",
    relevance_score: float = 0.9,
    confidence: float = 0.8,
) -> dict:
    return {
        "news_id": "news-1",
        "duplicate_group_id": "dup-1",
        "source": "Fixture",
        "title": "Synthetic signal headline",
        "url": "https://example.com/news",
        "published_at_utc": "2026-01-15T00:00:00+00:00",
        "retrieved_at_utc": "2026-01-15T00:05:00+00:00",
        "taiwan_trading_date": "2026-01-15",
        "sector": sector,
        "theme": theme,
        "us_tickers": us_tickers,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "relevance_label": relevance_label,
        "relevance_score": relevance_score,
        "confidence": confidence,
        "classification_method": "rule_based_v1",
        "matched_rules": "ticker:NVDA:nvidia",
        "reasoning_short": "Synthetic classifier reasoning.",
    }


def test_parse_pipe_or_json_list_handles_supported_serializations():
    assert parse_pipe_or_json_list("NVDA|AMD") == ["NVDA", "AMD"]
    assert parse_pipe_or_json_list('["NVDA", "AMD"]') == ["NVDA", "AMD"]
    assert parse_pipe_or_json_list("['NVDA', 'AMD']") == ["NVDA", "AMD"]


def test_positive_nvda_signal_maps_to_taiwan_target():
    mapping_df = load_mapping_table()

    rows = map_signal_row(_signal("NVDA"), mapping_df)

    assert rows
    assert any(row["taiwan_target_type"] == "ticker" for row in rows)


def test_positive_nvda_signal_produces_potentially_positive_impact():
    mapping_df = load_mapping_table()

    rows = map_signal_row(_signal("NVDA"), mapping_df)

    assert {row["directional_impact_label"] for row in rows} == {"potentially_positive"}


def test_negative_amd_signal_produces_potentially_negative_impact():
    mapping_df = load_mapping_table()

    rows = map_signal_row(_signal("AMD", sentiment_label="negative", sentiment_score=-0.7), mapping_df)

    assert rows
    assert {row["directional_impact_label"] for row in rows} == {"potentially_negative"}


def test_aapl_signal_maps_to_apple_supply_chain_targets():
    mapping_df = load_mapping_table()

    rows = map_signal_row(
        _signal("AAPL", sector="Apple Supply Chain", theme="Apple hardware demand"),
        mapping_df,
    )

    assert rows
    assert any("Apple Supply Chain" in row["taiwan_sector"] for row in rows)


def test_irrelevant_signal_produces_no_rows_by_default():
    mapping_df = load_mapping_table()

    rows = map_signal_row(
        _signal(
            "NVDA",
            sentiment_label="irrelevant",
            sentiment_score=0,
            sector="Irrelevant",
            theme="irrelevant",
            relevance_label="irrelevant",
            relevance_score=0,
        ),
        mapping_df,
    )

    assert rows == []


def test_unknown_relevant_us_ticker_produces_one_unmapped_row():
    mapping_df = load_mapping_table()

    rows = map_signal_row(_signal("ZZZ"), mapping_df)

    assert len(rows) == 1
    assert rows[0]["taiwan_target_type"] == "unmapped"
    assert rows[0]["directional_impact_label"] == "unmapped"
    assert rows[0]["mapping_confidence"] == 0
    assert rows[0]["combined_confidence"] == 0
    assert rows[0]["impact_score"] == 0


def test_confidence_and_impact_scores_are_clamped():
    mapping_df = load_mapping_table()

    rows = map_signal_row(_signal("NVDA", sentiment_score=2, relevance_score=2, confidence=2), mapping_df)

    assert rows
    assert all(0 <= row["combined_confidence"] <= 1 for row in rows)
    assert all(-1 <= row["impact_score"] <= 1 for row in rows)


def test_no_output_reasoning_contains_forbidden_recommendation_terms():
    mapping_df = load_mapping_table()
    signal_df = pd.DataFrame([_signal("NVDA"), _signal("ZZZ")])

    candidates = map_signals_dataframe(signal_df, mapping_df)

    assert not candidates.empty
    for reasoning in candidates["reasoning_short"].str.lower():
        assert all(term not in reasoning for term in FORBIDDEN_REASONING_TERMS)
