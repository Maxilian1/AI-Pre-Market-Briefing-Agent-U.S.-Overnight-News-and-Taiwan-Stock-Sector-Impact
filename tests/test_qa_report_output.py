import subprocess
import sys

from scripts.qa_report_output import validate_report_text
from src.reporting.report_generator import render_markdown_report
from tests.test_report_generator import _candidates_df, _signals_df


def test_validate_report_text_passes_clean_report():
    report = render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15")

    errors, warnings = validate_report_text(report)

    assert errors == []
    assert warnings == []


def test_validate_report_text_fails_missing_sections_and_restricted_wording():
    report = "# Bad Report\n\nrestricted wording-Off\n"

    errors, _ = validate_report_text(report)

    assert errors
    assert any("restricted wording" in error for error in errors)
    assert any("missing required section" in error for error in errors)


def test_qa_report_output_script_passes_with_optional_inputs(tmp_path):
    report_path = tmp_path / "report.md"
    signals_path = tmp_path / "signals.csv"
    candidates_path = tmp_path / "candidates.csv"
    _signals_df().to_csv(signals_path, index=False)
    _candidates_df().to_csv(candidates_path, index=False)
    report_path.write_text(
        render_markdown_report(_signals_df(), _candidates_df(), report_date="2026-01-15"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/qa_report_output.py",
            "--report",
            str(report_path),
            "--signals",
            str(signals_path),
            "--candidates",
            str(candidates_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "report QA errors: 0" in result.stdout
    assert "count by sector/theme:" in result.stdout
    assert "top Taiwan targets:" in result.stdout


def test_qa_report_output_script_fails_bad_report(tmp_path):
    report_path = tmp_path / "bad_report.md"
    report_path.write_text("# Bad Report\n\nrestricted wording-Off\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/qa_report_output.py",
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "ERROR:" in result.stdout
