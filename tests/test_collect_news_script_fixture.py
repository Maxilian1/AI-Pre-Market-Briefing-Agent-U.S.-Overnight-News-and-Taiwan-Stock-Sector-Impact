import csv
import subprocess
import sys


def test_collect_news_script_fixture_creates_csv(tmp_path):
    output_path = tmp_path / "fixture_news.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/collect_news.py",
            "--mode",
            "fixture",
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
    assert "total rows:" in result.stdout
    assert "unique duplicate groups:" in result.stdout
    assert "missing published_at_utc:" in result.stdout

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert rows
    assert "news_id" in reader.fieldnames
    assert "source" in reader.fieldnames
    assert "title" in reader.fieldnames
    assert "duplicate_group_id" in reader.fieldnames
