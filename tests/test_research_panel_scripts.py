import subprocess
import sys

import pandas as pd

from src.config import FIXTURES_DATA_DIR


def _return_label_rows() -> list[dict]:
    base = {
        "taiwan_trading_date": "2026-01-15",
        "return_target": "2330.TW",
        "return_target_type": "ticker",
        "taiwan_target_type": "ticker",
        "taiwan_sector": "Semiconductor Foundry",
        "directional_impact_label": "neutral",
        "impact_score": 0.0,
        "combined_confidence": 0.5,
        "prev_close_to_open_return": 0.001,
        "open_to_close_return": 0.002,
        "close_to_close_return": 0.003,
        "next_close_to_close_return": 0.004,
        "return_data_available": True,
    }
    return [
        base,
        {**base, "taiwan_sector": "AI Server and ODM", "impact_score": 0.1, "directional_impact_label": "potentially_positive"},
        {**base, "return_target": "unmapped", "return_target_type": "unmapped", "taiwan_target_type": "unmapped", "return_data_available": False},
    ]


def test_build_research_panel_script_fixture(tmp_path):
    return_labels = tmp_path / "return_labels.csv"
    panel_path = tmp_path / "research_panel.csv"
    controls_path = tmp_path / "baseline_controls.csv"
    pd.DataFrame(_return_label_rows()).to_csv(return_labels, index=False)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_research_panel.py",
            "--return-labels",
            str(return_labels),
            "--prices",
            str(FIXTURES_DATA_DIR / "sample_prices_daily.csv"),
            "--output-panel",
            str(panel_path),
            "--output-controls",
            str(controls_path),
            "--label",
            "test_fixture",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert panel_path.exists()
    assert controls_path.exists()
    panel = pd.read_csv(panel_path)
    assert len(panel) == 1
    assert panel.iloc[0]["return_target"] == "2330.TW"
    assert "qqq_return" in panel.columns
    assert "panel rows: 1" in result.stdout
    assert "controls added: True" in result.stdout


def test_run_regression_diagnostics_script_with_synthetic_panel(tmp_path):
    panel_path = FIXTURES_DATA_DIR / "sample_research_panel_directional.csv"
    results_path = tmp_path / "regression_results.csv"
    report_path = tmp_path / "regression_diagnostics.md"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_regression_diagnostics.py",
            "--panel",
            str(panel_path),
            "--output-csv",
            str(results_path),
            "--output-md",
            str(report_path),
            "--label",
            "synthetic",
            "--min-obs",
            "20",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert results_path.exists()
    assert report_path.exists()
    results = pd.read_csv(results_path)
    report = report_path.read_text(encoding="utf-8")
    assert (results["status"] == "fitted").any()
    for section in [
        "Regression Diagnostics Summary",
        "Input Data",
        "Research Panel Construction",
        "Baseline Control Alignment",
        "Model Specifications",
        "Regression Results",
        "Insufficient Sample Warnings",
        "Interpretation Caveats",
        "Next Steps",
    ]:
        assert section in report
    assert "not investment advice" in report.lower()
    assert "out-of-sample validation is required" in report.lower()
    assert "fitted models:" in result.stdout
