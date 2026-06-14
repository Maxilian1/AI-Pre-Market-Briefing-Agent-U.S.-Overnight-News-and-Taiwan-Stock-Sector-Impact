import subprocess
import sys

import pandas as pd

from src.config import FIXTURES_DATA_DIR


FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "recommendation",
    "recommendations",
    "will rise",
    "will fall",
    "guaranteed",
    "target price",
    "must trade",
]


def test_run_oos_validation_script_with_synthetic_fixture(tmp_path):
    panel_path = FIXTURES_DATA_DIR / "sample_research_panel_oos.csv"
    results_path = tmp_path / "oos_validation_results.csv"
    report_path = tmp_path / "oos_validation_summary.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_oos_validation.py",
            "--panel",
            str(panel_path),
            "--output-csv",
            str(results_path),
            "--output-md",
            str(report_path),
            "--label",
            "synthetic_oos",
            "--data-mode",
            "synthetic",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert results_path.exists()
    assert report_path.exists()
    results = pd.read_csv(results_path)
    report = report_path.read_text(encoding="utf-8")
    lowered = report.lower()
    assert (results["status"] == "fitted").any()
    for section in [
        "Out-of-Sample Validation Summary",
        "Input Data",
        "Chronological Split Method",
        "Model Families",
        "Baseline vs News Model Comparison",
        "Insufficient Sample Warnings",
        "Interpretation Caveats",
        "Next Steps",
    ]:
        assert section in report
    assert "this is not investment advice" in lowered
    assert "look-ahead bias controls depend on correct timestamps" in lowered
    assert all(term not in lowered for term in FORBIDDEN_TERMS)
    assert "fitted validations:" in result.stdout
