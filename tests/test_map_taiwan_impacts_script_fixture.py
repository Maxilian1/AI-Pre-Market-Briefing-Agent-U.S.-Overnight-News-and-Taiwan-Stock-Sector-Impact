import csv
import subprocess
import sys

from src.universe import TAIWAN_TICKERS


REQUIRED_OUTPUT_COLUMNS = {
    "news_id",
    "duplicate_group_id",
    "source",
    "title",
    "url",
    "published_at_utc",
    "retrieved_at_utc",
    "taiwan_trading_date",
    "sector",
    "theme",
    "us_tickers",
    "sentiment_label",
    "sentiment_score",
    "relevance_label",
    "relevance_score",
    "signal_confidence",
    "taiwan_target",
    "taiwan_target_type",
    "taiwan_ticker",
    "taiwan_company",
    "taiwan_sector",
    "relationship_type",
    "mapping_confidence",
    "assumption_flag",
    "mapping_notes",
    "directional_impact_label",
    "impact_score",
    "combined_confidence",
    "mapping_method",
    "reasoning_short",
}


def test_map_taiwan_impacts_script_fixture_pipeline(tmp_path):
    raw_path = tmp_path / "raw_news.csv"
    signals_path = tmp_path / "news_signals.csv"
    candidates_path = tmp_path / "taiwan_impact_candidates.csv"

    subprocess.run(
        [
            sys.executable,
            "scripts/collect_news.py",
            "--mode",
            "fixture",
            "--date",
            "2026-01-15",
            "--output",
            str(raw_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/classify_news.py",
            "--input",
            str(raw_path),
            "--date",
            "2026-01-15",
            "--output",
            str(signals_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/map_taiwan_impacts.py",
            "--input",
            str(signals_path),
            "--date",
            "2026-01-15",
            "--output",
            str(candidates_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert candidates_path.exists()
    assert "total input signals: 8" in result.stdout
    assert "total mapped candidate rows:" in result.stdout

    with candidates_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert rows
    assert REQUIRED_OUTPUT_COLUMNS.issubset(set(reader.fieldnames or []))
    assert {row["mapping_method"] for row in rows} == {"seed_mapping_v1"}

    allowed_targets = set(TAIWAN_TICKERS)
    for row in rows:
        ticker = row["taiwan_ticker"]
        assert (
            ticker in allowed_targets
            or ticker.startswith("BASKET:")
            or ticker.startswith("PROXY:")
            or ticker == ""
        )

    assert any("NVDA" in row["us_tickers"] and row["taiwan_ticker"] for row in rows)
