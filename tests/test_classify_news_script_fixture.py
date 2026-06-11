import csv
import subprocess
import sys


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
    "confidence",
    "classification_method",
    "matched_rules",
    "reasoning_short",
}


def test_classify_news_script_fixture_creates_signal_csv_without_duplicate_inflation(tmp_path):
    raw_path = tmp_path / "raw_news.csv"
    output_path = tmp_path / "news_signals.csv"

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

    result = subprocess.run(
        [
            sys.executable,
            "scripts/classify_news.py",
            "--input",
            str(raw_path),
            "--date",
            "2026-01-15",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output_path.exists()
    assert "total raw rows: 10" in result.stdout
    assert "total classified rows: 8" in result.stdout
    assert "duplicate groups removed: 2" in result.stdout

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert rows
    assert REQUIRED_OUTPUT_COLUMNS.issubset(set(reader.fieldnames or []))
    assert {row["classification_method"] for row in rows} == {"rule_based_v1"}
    assert len(rows) == 8
