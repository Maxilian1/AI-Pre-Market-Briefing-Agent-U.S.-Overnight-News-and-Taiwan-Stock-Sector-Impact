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


def _section(report: str, header: str) -> str:
    start = report.index(f"## {header}")
    next_start = report.find("\n## ", start + 1)
    if next_start == -1:
        return report[start:]
    return report[start:next_start]


def _with_title(df: pd.DataFrame, title: str) -> pd.DataFrame:
    updated = df.copy()
    updated["title"] = title
    return updated


def test_render_markdown_report_returns_string():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    assert isinstance(report, str)


def test_report_contains_required_section_headers():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    for header in [
        "Executive Summary",
        "Overnight U.S. News Themes",
        "Market Context Signals",
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

    assert "External headline: Nvidia AI server demand lifts attention on accelerator supply chain" in report
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


def test_report_labels_external_selloff_headline_without_awkward_redaction():
    title = "3 Beaten-Down AI Chip Stocks Worth a Closer Look After the Sell-Off"
    report = render_markdown_report(
        _with_title(_signals_df(), title),
        _with_title(_candidates_df(), title),
        report_date="2026-01-15",
    )

    assert "restricted wording-Off" not in report
    assert "restricted wording" not in report
    assert f"External headline: {title}" in report


def test_report_aggregates_taiwan_watchlist_candidates():
    candidates = pd.concat(
        [
            _candidates_df(),
            _candidates_df().assign(
                news_id="news-2",
                duplicate_group_id="dup-2",
                title="Nvidia accelerator supply update supports AI server theme",
                impact_score=0.2,
                combined_confidence=0.6,
            ),
        ],
        ignore_index=True,
    )

    report = render_markdown_report(_signals_df(), candidates, report_date="2026-01-15")
    watchlist = _section(report, "Taiwan Watchlist Candidates")

    assert "candidate_count 2" in watchlist
    assert watchlist.count("- 2330.TW TSMC:") == 1
    assert "External headline: Nvidia accelerator supply update supports AI server theme" in watchlist


def test_report_contains_market_context_section_with_caveat_and_examples():
    signals = pd.DataFrame(
        [
            {
                **_signals_df().iloc[0].to_dict(),
                "news_id": "macro-1",
                "title": "Fed officials discuss rate outlook ahead of inflation data",
                "sector": "Macro",
                "theme": "interest rates / Fed",
            },
            {
                **_signals_df().iloc[0].to_dict(),
                "news_id": "energy-1",
                "title": "Oil prices steady as traders weigh shipping risks",
                "sector": "Energy",
                "theme": "oil / energy",
            },
        ]
    )

    report = render_markdown_report(signals, _candidates_df(), report_date="2026-01-15")

    assert "## Market Context Signals" in report
    assert "These are market context signals and are not direct Taiwan company mappings." in report
    assert "External headline: Fed officials discuss rate outlook ahead of inflation data" in report
    assert "External headline: Oil prices steady as traders weigh shipping risks" in report


def test_market_context_unmapped_candidates_are_not_mixed_into_watchlist_review():
    base = _candidates_df().iloc[0].to_dict()
    candidates = pd.DataFrame(
        [
            {
                **base,
                "news_id": "macro-candidate",
                "title": "Fed officials discuss rate outlook ahead of inflation data",
                "sector": "Macro",
                "theme": "interest rates / Fed",
                "taiwan_target": "unmapped",
                "taiwan_target_type": "unmapped",
                "taiwan_ticker": "",
                "taiwan_company": "",
                "taiwan_sector": "",
                "directional_impact_label": "unmapped",
                "impact_score": 0.0,
                "combined_confidence": 0.0,
            },
            {
                **base,
                "news_id": "unknown-equity",
                "title": "Unknown AI chip supplier reports new accelerator demand",
                "sector": "Semiconductor",
                "theme": "AI chip demand",
                "taiwan_target": "unmapped",
                "taiwan_target_type": "unmapped",
                "taiwan_ticker": "",
                "taiwan_company": "",
                "taiwan_sector": "",
                "directional_impact_label": "unmapped",
                "impact_score": 0.0,
                "combined_confidence": 0.0,
            },
        ]
    )

    report = render_markdown_report(_signals_df(), candidates, report_date="2026-01-15")
    watchlist = _section(report, "Taiwan Watchlist Candidates")
    review = _section(report, "Neutral / Unmapped / Requires Review")

    assert "candidate_count 1" in watchlist
    assert "Unknown AI chip supplier reports new accelerator demand" in watchlist
    assert "Fed officials discuss rate outlook ahead of inflation data" not in watchlist
    assert "Market context candidate groups summarized above: 1" in review
