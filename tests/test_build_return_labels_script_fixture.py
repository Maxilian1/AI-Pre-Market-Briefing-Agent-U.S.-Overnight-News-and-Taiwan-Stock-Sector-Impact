import subprocess
import sys

import pandas as pd

from src.market_data.return_labels import REQUIRED_RETURN_LABEL_COLUMNS


def _candidate_rows() -> list[dict]:
    base = {
        "taiwan_trading_date": "2026-01-15",
        "taiwan_company": "Fixture Company",
        "taiwan_sector": "Fixture Sector",
        "directional_impact_label": "neutral",
        "impact_score": 0.0,
        "combined_confidence": 0.5,
    }
    return [
        {
            **base,
            "taiwan_target": "2330.TW TSMC",
            "taiwan_target_type": "ticker",
            "taiwan_ticker": "2330.TW",
        },
        {
            **base,
            "taiwan_target": "BASKET:TW_SEMICONDUCTOR",
            "taiwan_target_type": "basket",
            "taiwan_ticker": "BASKET:TW_SEMICONDUCTOR",
        },
        {
            **base,
            "taiwan_target": "Nasdaq / QQQ Control",
            "taiwan_target_type": "proxy",
            "taiwan_ticker": "PROXY:QQQ",
        },
        {
            **base,
            "taiwan_target": "unmapped",
            "taiwan_target_type": "unmapped",
            "taiwan_ticker": "",
            "directional_impact_label": "unmapped",
        },
    ]


def test_build_return_labels_script_fixture(tmp_path):
    candidates_path = tmp_path / "candidates.csv"
    prices_path = tmp_path / "prices_fixture.csv"
    labels_path = tmp_path / "return_labels.csv"
    pd.DataFrame(_candidate_rows()).to_csv(candidates_path, index=False)

    download_result = subprocess.run(
        [
            sys.executable,
            "scripts/download_market_data.py",
            "--mode",
            "fixture",
            "--start",
            "2026-01-12",
            "--end",
            "2026-01-20",
            "--output",
            str(prices_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert prices_path.exists()
    assert "missing tickers: none" in download_result.stdout

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_return_labels.py",
            "--candidates",
            str(candidates_path),
            "--prices",
            str(prices_path),
            "--date",
            "2026-01-15",
            "--output",
            str(labels_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert labels_path.exists()
    labels = pd.read_csv(labels_path)
    assert set(REQUIRED_RETURN_LABEL_COLUMNS).issubset(labels.columns)
    assert labels["return_data_available"].fillna(False).astype(bool).any()
    unavailable = labels[labels["taiwan_target_type"].isin(["proxy", "unmapped"])]
    assert not unavailable.empty
    assert not unavailable["return_data_available"].fillna(False).astype(bool).any()
    assert "return label rows: 4" in result.stdout
