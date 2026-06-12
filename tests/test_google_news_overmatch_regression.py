import json
from pathlib import Path

from src.signals.rule_based_classifier import classify_news_row


def _cases():
    return json.loads(Path("data/fixtures/google_news_overmatch_cases.json").read_text(encoding="utf-8"))


def _case_by_title_prefix(prefix: str) -> dict:
    for case in _cases():
        if case["title"].startswith(prefix):
            return case
    raise AssertionError(f"Missing fixture case: {prefix}")


def test_google_news_oil_case_classifies_as_energy_not_cloud():
    result = classify_news_row(_case_by_title_prefix("Oil prices")).to_dict()

    assert result["sector"] == "Energy"
    assert result["theme"] == "oil / energy"
    assert "GOOGL" not in result["us_tickers"]
    assert "ticker:GOOGL:google" not in result["matched_rules"]
    assert "sector:Cloud / Data Center:google" not in result["matched_rules"]


def test_google_news_fed_case_classifies_as_macro_not_cloud():
    result = classify_news_row(_case_by_title_prefix("Fed officials")).to_dict()

    assert result["sector"] == "Macro"
    assert result["theme"] == "interest rates / Fed"
    assert "GOOGL" not in result["us_tickers"]


def test_google_news_sports_case_classifies_as_irrelevant():
    result = classify_news_row(_case_by_title_prefix("Local sports")).to_dict()

    assert result["sector"] == "Irrelevant"
    assert result["theme"] == "irrelevant"
    assert result["relevance_score"] == 0
    assert result["sentiment_label"] == "irrelevant"


def test_google_news_nvidia_case_does_not_trigger_googl():
    result = classify_news_row(_case_by_title_prefix("Nvidia")).to_dict()

    assert result["sector"] in {"Semiconductor", "AI Infrastructure"}
    assert "NVDA" in result["us_tickers"]
    assert "GOOGL" not in result["us_tickers"]
    assert "ticker:GOOGL:google" not in result["matched_rules"]


def test_google_news_amd_case_does_not_trigger_googl():
    result = classify_news_row(_case_by_title_prefix("AMD")).to_dict()

    assert result["sector"] in {"Semiconductor", "AI Infrastructure"}
    assert "AMD" in result["us_tickers"]
    assert "GOOGL" not in result["us_tickers"]


def test_google_cloud_contextual_case_triggers_googl_and_cloud_sector():
    result = classify_news_row(_case_by_title_prefix("Google Cloud")).to_dict()

    assert result["sector"] == "Cloud / Data Center"
    assert result["theme"] == "data center capex"
    assert "GOOGL" in result["us_tickers"]


def test_google_news_and_url_alone_do_not_trigger_googl():
    result = classify_news_row(
        {
            "news_id": "provider-only",
            "duplicate_group_id": "provider-only",
            "source": "Google News RSS - Oil Energy Query",
            "title": "Google News",
            "url": "https://news.google.com/rss/articles/provider-only",
            "published_at_utc": "2026-06-11T00:00:00+00:00",
            "retrieved_at_utc": "2026-06-11T00:05:00+00:00",
            "raw_summary": '<a href="https://news.google.com/rss/articles/provider-only">Google News</a>',
        }
    ).to_dict()

    assert "GOOGL" not in result["us_tickers"]
    assert "ticker:GOOGL:google" not in result["matched_rules"]
    assert "sector:Cloud / Data Center:google" not in result["matched_rules"]
