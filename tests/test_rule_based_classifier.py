import pandas as pd

from src.signals.rule_based_classifier import classify_headline, classify_news_dataframe
from src.signals.rules import VALID_RELEVANCE_LABELS, VALID_SENTIMENT_LABELS


def test_nvidia_ai_server_headline_is_relevant_and_includes_nvda():
    result = classify_headline("Nvidia AI server demand rises on strong accelerator orders")

    assert result["sector"] in {"Semiconductor", "AI Infrastructure"}
    assert "NVDA" in result["us_tickers"]
    assert result["relevance_label"] in {"high", "medium"}


def test_amd_headline_includes_amd():
    result = classify_headline("AMD launches MI350 accelerator for data center customers")

    assert "AMD" in result["us_tickers"]
    assert result["classification_method"] == "rule_based_v1"


def test_apple_iphone_demand_headline_classifies_as_apple_supply_chain():
    result = classify_headline("Apple iPhone demand rises after updated hardware reports")

    assert result["sector"] == "Apple Supply Chain"
    assert result["theme"] == "Apple hardware demand"
    assert "AAPL" in result["us_tickers"]


def test_micron_memory_headline_classifies_as_memory_and_includes_mu():
    result = classify_headline("Micron memory outlook improves as DRAM orders surge")

    assert result["sector"] == "Memory"
    assert result["theme"] == "memory cycle"
    assert "MU" in result["us_tickers"]


def test_sram_ai_world_headline_is_not_irrelevant():
    result = classify_headline("Why SRAM Chips Are Pulling Ahead in the New AI World")

    assert result["sector"] in {"Memory", "Semiconductor"}
    assert result["theme"] in {"memory cycle", "AI chip demand", "semiconductor market movement"}


def test_ai_chip_stocks_after_selloff_is_not_irrelevant():
    result = classify_headline("3 Beaten-Down AI Chip Stocks Worth a Closer Look After the Sell-Off")

    assert result["sector"] == "Semiconductor"
    assert result["theme"] in {"AI chip demand", "semiconductor market movement"}


def test_ad_like_homepage_title_remains_irrelevant():
    result = classify_headline("AI Investing Insights - Official Homepage")

    assert result["sector"] == "Irrelevant"
    assert result["theme"] == "irrelevant"
    assert result["relevance_score"] == 0


def test_sk_hynix_nvidia_memory_partnership_is_domain_relevant():
    result = classify_headline("SK hynix and NVIDIA announce multi-year memory partnership")

    assert result["sector"] in {"Memory", "Semiconductor"}
    assert result["theme"] == "memory cycle"
    assert "NVDA" in result["us_tickers"]


def test_fed_rate_headline_classifies_as_macro():
    result = classify_headline("Fed officials discuss rate outlook before inflation data")

    assert result["sector"] == "Macro"
    assert result["theme"] == "interest rates / Fed"


def test_macro_summary_does_not_trigger_apple_mac_keyword():
    result = classify_headline(
        "Fed officials discuss rate outlook ahead of inflation data",
        raw_summary="Sample metadata-only macro summary.",
    )

    assert result["sector"] == "Macro"
    assert "AAPL" not in result["us_tickers"]


def test_oil_headline_classifies_as_energy():
    result = classify_headline("Oil prices rise as crude traders monitor shipping risks")

    assert result["sector"] == "Energy"
    assert result["theme"] == "oil / energy"


def test_irrelevant_headline_has_zero_relevance():
    result = classify_headline("Local sports team announces spring training schedule")

    assert result["sector"] == "Irrelevant"
    assert result["theme"] == "irrelevant"
    assert result["sentiment_label"] == "irrelevant"
    assert result["relevance_score"] == 0


def test_negative_guidance_headline_has_negative_sentiment():
    result = classify_headline("Nvidia cuts guidance after weak demand")

    assert result["sentiment_label"] == "negative"
    assert result["sentiment_score"] < 0


def test_positive_strong_demand_headline_has_positive_sentiment():
    result = classify_headline("Nvidia rises on strong AI chip demand")

    assert result["sentiment_label"] == "positive"
    assert result["sentiment_score"] > 0


def test_google_news_alone_does_not_trigger_googl():
    result = classify_headline("Google News")

    assert "GOOGL" not in result["us_tickers"]
    assert result["sector"] == "Irrelevant"


def test_google_cloud_triggers_googl_and_cloud_data_center():
    result = classify_headline("Google Cloud announces data center expansion")

    assert "GOOGL" in result["us_tickers"]
    assert result["sector"] == "Cloud / Data Center"
    assert result["theme"] == "data center capex"


def test_alphabet_cloud_capex_triggers_googl_and_cloud_data_center():
    result = classify_headline("Alphabet raises cloud capex guidance")

    assert "GOOGL" in result["us_tickers"]
    assert result["sector"] == "Cloud / Data Center"
    assert result["theme"] == "data center capex"


def test_no_cloud_data_center_with_oil_energy_theme():
    result = classify_headline("Oil prices steady as traders weigh shipping risks")

    assert not (result["sector"] == "Cloud / Data Center" and result["theme"] == "oil / energy")


def test_no_cloud_data_center_with_interest_rates_theme():
    result = classify_headline("Fed officials discuss rate outlook ahead of inflation data")

    assert not (result["sector"] == "Cloud / Data Center" and result["theme"] == "interest rates / Fed")


def test_no_cloud_data_center_with_irrelevant_theme():
    result = classify_headline("Local sports team announces spring training schedule")

    assert not (result["sector"] == "Cloud / Data Center" and result["theme"] == "irrelevant")


def test_semiconductor_headline_without_specific_theme_gets_default_market_theme():
    result = classify_headline("Semiconductor stocks report outlook")

    assert result["sector"] == "Semiconductor"
    assert result["theme"] == "semiconductor market movement"


def test_ai_infrastructure_headline_without_specific_theme_gets_default_theme():
    result = classify_headline("AI infrastructure plans expansion")

    assert result["sector"] == "AI Infrastructure"
    assert result["theme"] == "AI infrastructure"


def test_classification_labels_and_scores_stay_in_allowed_ranges():
    result = classify_headline("Micron memory reports inventory correction")

    assert result["sentiment_label"] in VALID_SENTIMENT_LABELS
    assert result["relevance_label"] in VALID_RELEVANCE_LABELS
    assert -1 <= result["sentiment_score"] <= 1
    assert 0 <= result["relevance_score"] <= 1
    assert 0 <= result["confidence"] <= 1


def test_dataframe_dedupe_keeps_earliest_published_representative():
    raw_df = pd.DataFrame(
        [
            {
                "news_id": "late",
                "duplicate_group_id": "group-1",
                "source": "Fixture",
                "title": "Nvidia reports AI chip demand late",
                "url": "https://example.com/late",
                "published_at_utc": "2026-01-15T02:00:00+00:00",
                "retrieved_at_utc": "2026-01-15T02:05:00+00:00",
                "raw_summary": "",
            },
            {
                "news_id": "early",
                "duplicate_group_id": "group-1",
                "source": "Fixture",
                "title": "Nvidia reports AI chip demand early",
                "url": "https://example.com/early",
                "published_at_utc": "2026-01-15T01:00:00+00:00",
                "retrieved_at_utc": "2026-01-15T01:05:00+00:00",
                "raw_summary": "",
            },
        ]
    )

    signals = classify_news_dataframe(raw_df)

    assert len(signals) == 1
    assert signals.iloc[0]["news_id"] == "early"
