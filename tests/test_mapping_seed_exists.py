import csv
from pathlib import Path

from src.universe import TAIWAN_TICKERS


REQUIRED_COLUMNS = {
    "us_ticker",
    "us_company",
    "theme",
    "taiwan_ticker",
    "taiwan_company",
    "taiwan_sector",
    "relationship_type",
    "confidence",
    "assumption_flag",
    "notes",
}


def test_mapping_seed_file_exists():
    path = Path("data/processed/ticker_mapping_seed.csv")

    assert path.exists()


def test_mapping_seed_has_required_columns():
    path = Path("data/processed/ticker_mapping_seed.csv")

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        assert REQUIRED_COLUMNS.issubset(set(reader.fieldnames or []))


def test_mapping_seed_taiwan_tickers_are_known_or_documented_proxies():
    path = Path("data/processed/ticker_mapping_seed.csv")
    known_tickers = set(TAIWAN_TICKERS)

    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows
    for row in rows:
        taiwan_ticker = row["taiwan_ticker"]
        is_known_ticker = taiwan_ticker in known_tickers
        is_documented_proxy = taiwan_ticker.startswith("PROXY:") and "proxy" in row["notes"].lower()

        assert is_known_ticker or is_documented_proxy


def test_mapping_seed_assumption_flag_is_populated():
    path = Path("data/processed/ticker_mapping_seed.csv")

    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows
    for row in rows:
        assert row["assumption_flag"] in {"True", "False"}
