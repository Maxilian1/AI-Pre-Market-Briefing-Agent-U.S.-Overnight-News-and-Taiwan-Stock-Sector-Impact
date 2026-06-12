import subprocess
import sys

import pandas as pd


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


def _return_label_rows() -> list[dict]:
    base = {
        "taiwan_trading_date": "2026-01-15",
        "return_target": "2330.TW",
        "return_target_type": "ticker",
        "taiwan_target_type": "ticker",
        "taiwan_sector": "Semiconductor Foundry",
        "combined_confidence": 0.6,
        "prev_close_to_open_return": 0.01,
        "open_to_close_return": 0.02,
        "close_to_close_return": 0.03,
        "next_close_to_close_return": 0.04,
        "return_data_available": True,
    }
    return [
        {**base, "directional_impact_label": "potentially_positive", "impact_score": 0.2},
        {**base, "directional_impact_label": "neutral", "impact_score": 0.0},
        {
            **base,
            "return_target": "2454.TW",
            "taiwan_sector": "Semiconductor Design",
            "directional_impact_label": "potentially_negative",
            "impact_score": -0.1,
            "open_to_close_return": -0.01,
        },
        {
            **base,
            "return_target": "unmapped",
            "return_target_type": "unmapped",
            "taiwan_target_type": "unmapped",
            "taiwan_sector": "",
            "directional_impact_label": "unmapped",
            "impact_score": 0.0,
            "return_data_available": False,
            "open_to_close_return": pd.NA,
        },
    ]


def test_run_event_study_script_fixture_outputs(tmp_path):
    return_labels_path = tmp_path / "return_labels.csv"
    results_path = tmp_path / "event_study_results.csv"
    aggregated_path = tmp_path / "event_study_aggregated.csv"
    summary_path = tmp_path / "event_study_summary.md"
    pd.DataFrame(_return_label_rows()).to_csv(return_labels_path, index=False)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_event_study.py",
            "--return-labels",
            str(return_labels_path),
            "--output-csv",
            str(results_path),
            "--output-aggregated",
            str(aggregated_path),
            "--output-md",
            str(summary_path),
            "--date",
            "2026-01-15",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert results_path.exists()
    assert aggregated_path.exists()
    assert summary_path.exists()
    assert "input rows: 4" in result.stdout
    assert "aggregated rows: 3" in result.stdout

    results = pd.read_csv(results_path)
    aggregated = pd.read_csv(aggregated_path)
    report = summary_path.read_text(encoding="utf-8")

    assert not results.empty
    assert not aggregated.empty
    for section in [
        "Event Study Summary",
        "Input Data",
        "Aggregation Method",
        "Aggregated Signal Counts",
        "Return Bucket Summary",
        "Directional Hit Ratio",
        "Statistical Caveats",
        "Limitations",
        "Next Steps",
    ]:
        assert section in report

    lowered = report.lower()
    assert "small samples are not statistically reliable" in lowered
    assert "not investment advice" in lowered
    assert "returns are outcome labels and were not used to generate signals" in lowered
    assert all(term not in lowered for term in FORBIDDEN_TERMS)
