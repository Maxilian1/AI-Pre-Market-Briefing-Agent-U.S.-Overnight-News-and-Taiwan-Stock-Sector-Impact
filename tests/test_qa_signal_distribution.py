import csv
import subprocess
import sys


def test_qa_script_passes_on_clean_fixture(tmp_path):
    raw_path = tmp_path / "raw_news.csv"
    signals_path = tmp_path / "news_signals.csv"

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
        [sys.executable, "scripts/qa_signal_distribution.py", "--signals", str(signals_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "suspicious Cloud/theme rows: 0" in result.stdout
    assert "GOOGL matched-rule count: 0" in result.stdout


def test_qa_script_fails_on_bad_cloud_oil_and_googl_rules(tmp_path):
    bad_path = tmp_path / "bad_signals.csv"
    with bad_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["source", "sector", "theme", "matched_rules"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source": "Google News RSS - Oil Energy Query",
                "sector": "Cloud / Data Center",
                "theme": "oil / energy",
                "matched_rules": "ticker:GOOGL:google|sector:Cloud / Data Center:google",
            }
        )

    result = subprocess.run(
        [sys.executable, "scripts/qa_signal_distribution.py", "--signals", str(bad_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "suspicious Cloud/theme rows: 1" in result.stdout
    assert "GOOGL matched-rule count: 2" in result.stdout
