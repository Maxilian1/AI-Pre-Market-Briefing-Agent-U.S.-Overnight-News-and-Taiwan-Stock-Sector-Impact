import subprocess
import sys

import pytest

from src.cli_utils import validate_iso_date


def test_validate_iso_date_accepts_real_iso_date():
    assert validate_iso_date("2026-01-15") == "2026-01-15"


@pytest.mark.parametrize("bad_date", ["YYYY-MM-DD", "yyyymmdd", "DATE", "today", "null", "none", "2026-13-40"])
def test_validate_iso_date_rejects_placeholders_and_malformed_dates(bad_date):
    with pytest.raises(ValueError):
        validate_iso_date(bad_date)


def test_collect_news_invalid_date_exits_nonzero_without_output(tmp_path):
    output_path = tmp_path / "should_not_exist.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/collect_news.py",
            "--mode",
            "fixture",
            "--date",
            "YYYY-MM-DD",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not output_path.exists()


@pytest.mark.parametrize(
    "command",
    [
        ["scripts/classify_news.py", "--input", "missing.csv", "--date", "today"],
        ["scripts/map_taiwan_impacts.py", "--input", "missing.csv", "--date", "YYYY-MM-DD"],
        [
            "scripts/generate_report.py",
            "--signals",
            "missing_signals.csv",
            "--candidates",
            "missing_candidates.csv",
            "--date",
            "DATE",
        ],
    ],
)
def test_other_cli_scripts_reject_invalid_date_before_io(command):
    result = subprocess.run([sys.executable, *command], capture_output=True, text=True)

    assert result.returncode != 0
    assert "invalid" in result.stderr.lower()
