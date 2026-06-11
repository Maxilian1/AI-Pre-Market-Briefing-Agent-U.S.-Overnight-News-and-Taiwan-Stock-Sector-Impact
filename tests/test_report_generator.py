import pandas as pd

from src.reporting.report_generator import render_markdown_report


FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "guaranteed",
    "will rise",
    "will fall",
    "target price",
    "must trade",
]


def _signals_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "news_id": "news-1",
                "duplicate_group_id": "dup-1",
                "source": "Synthetic Fixture Wire",
                "title": "Nvidia AI server demand lifts attention on accelerator supply chain",
                "url": "https://example.com/news/nvidia-ai-server-demand",
                "published_at_utc": "2026-01-14T22:15:00+00:00",
                "retrieved_at_utc": "2026-01-15T00:30:00+00:00",
                "taiwan_trading_date": "2026-01-15",
                "sector": "AI Infrastructure",
                "theme": "AI chip demand",
                "us_tickers": "NVDA",
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "relevance_label": "high",
                "relevance_score": 0.9,
                "confidence": 0.9,
            }
        ]
    )


def _candidates_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "news_id": "news-1",
                "duplicate_group_id": "dup-1",
                "source": "Synthetic Fixture Wire",
                "title": "Nvidia AI server demand lifts attention on accelerator supply chain",
                "url": "https://example.com/news/nvidia-ai-server-demand",
                "published_at_utc": "2026-01-14T22:15:00+00:00",
                "retrieved_at_utc": "2026-01-15T00:30:00+00:00",
                "taiwan_trading_date": "2026-01-15",
                "sector": "AI Infrastructure",
                "theme": "AI chip demand",
                "us_tickers": "NVDA",
                "sentiment_label": "neutral",
                "sentiment_score": 0.0,
                "relevance_label": "high",
                "relevance_score": 0.9,
                "signal_confidence": 0.9,
                "taiwan_target": "2330.TW TSMC",
                "taiwan_target_type": "ticker",
                "taiwan_ticker": "2330.TW",
                "taiwan_company": "TSMC",
                "taiwan_sector": "Semiconductor Foundry",
                "relationship_type": "supplier/customer/sector read-through",
                "mapping_confidence": 0.6,
                "assumption_flag": "True",
                "mapping_notes": "Seed research assumption; requires validation.",
                "directional_impact_label": "neutral",
                "impact_score": 0.0,
                "combined_confidence": 0.54,
                "mapping_method": "seed_mapping_v1",
                "reasoning_short": "Deterministic seed mapping matched NVDA to 2330.TW.",
            }
        ]
    )


def test_render_markdown_report_returns_string():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    assert isinstance(report, str)


def test_report_contains_required_section_headers():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    for header in [
        "Executive Summary",
        "Overnight U.S. News Themes",
        "Taiwan Watchlist Candidates",
        "Potentially Positive Candidates",
        "Potentially Negative Candidates",
        "Neutral / Unmapped / Requires Review",
        "Source Provenance",
        "Limitations",
    ]:
        assert header in report


def test_report_contains_non_investment_advice_disclaimer():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    assert "not investment advice" in report.lower()
    assert "requires validation" in report.lower()


def test_report_does_not_contain_forbidden_terms():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")
    lowered = report.lower()

    assert all(term not in lowered for term in FORBIDDEN_TERMS)


def test_report_includes_representative_headline_when_signals_are_provided():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    assert "Nvidia AI server demand lifts attention on accelerator supply chain" in report
    assert "Synthetic Fixture Wire" in report


def test_report_names_taiwan_targets_baskets_and_sectors():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")
    lowered = report.lower()

    assert "taiwan targets" in lowered
    assert "basket" in lowered
    assert "semiconductor foundry" in lowered


def test_report_declares_csv_basis_and_no_llm_generation():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")
    lowered = report.lower()

    assert "signals csv" in lowered
    assert "taiwan impact candidates csv" in lowered
    assert "no llm generation" in lowered


def test_report_uses_cautious_directional_vocabulary():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")
    lowered = report.lower()

    assert "potentially positive" in lowered
    assert "potentially negative" in lowered
    assert "neutral" in lowered


def test_report_handles_empty_candidates_gracefully():
    report = render_markdown_report(_signals_df(), pd.DataFrame(), report_date="2026-01-15")

    assert "No Taiwan impact candidates were generated." in report
    assert "Executive Summary" in report
