import pandas as pd

from src.backtest.research_panel import (
    add_directional_dummies,
    build_target_day_panel,
    load_return_label_files,
    validate_panel,
)


def _return_label(
    date: str = "2026-01-15",
    target: str = "2330.TW",
    label: str = "potentially_positive",
    impact: float = 0.2,
    available: bool = True,
    sector: str = "Semiconductor Foundry",
) -> dict:
    return {
        "taiwan_trading_date": date,
        "return_target": target,
        "return_target_type": "ticker",
        "taiwan_target_type": "ticker",
        "taiwan_sector": sector,
        "directional_impact_label": label,
        "impact_score": impact,
        "combined_confidence": 0.6,
        "prev_close_to_open_return": 0.01,
        "open_to_close_return": 0.02,
        "close_to_close_return": 0.03,
        "next_close_to_close_return": 0.04,
        "return_data_available": available,
    }


def test_multiple_return_label_files_combine(tmp_path):
    first = tmp_path / "return_labels_1.csv"
    second = tmp_path / "return_labels_2.csv"
    pd.DataFrame([_return_label(target="2330.TW")]).to_csv(first, index=False)
    pd.DataFrame([_return_label(target="2454.TW")]).to_csv(second, index=False)

    combined = load_return_label_files([first, second])

    assert len(combined) == 2
    assert set(combined["return_target"]) == {"2330.TW", "2454.TW"}


def test_target_day_panel_has_one_row_per_date_return_target():
    labels = pd.DataFrame(
        [
            _return_label(target="2382.TW", sector="AI Server and ODM", impact=0.1),
            _return_label(target="2382.TW", sector="Apple Supply Chain", impact=0.0, label="neutral"),
        ]
    )

    panel = build_target_day_panel(labels)

    assert len(panel) == 1
    assert panel.iloc[0]["candidate_count"] == 2
    assert panel.iloc[0]["sum_impact_score"] == 0.1
    assert "AI Server and ODM" in panel.iloc[0]["taiwan_sector"]
    assert "Apple Supply Chain" in panel.iloc[0]["taiwan_sector"]


def test_directional_dummies_are_correct():
    panel = pd.DataFrame(
        [
            {"final_directional_label": "potentially_positive"},
            {"final_directional_label": "potentially_negative"},
            {"final_directional_label": "neutral"},
        ]
    )

    with_dummies = add_directional_dummies(panel)

    assert with_dummies["is_potentially_positive"].tolist() == [1, 0, 0]
    assert with_dummies["is_potentially_negative"].tolist() == [0, 1, 0]
    assert with_dummies["is_neutral"].tolist() == [0, 0, 1]


def test_unavailable_return_rows_are_excluded_by_default():
    labels = pd.DataFrame(
        [
            _return_label(target="2330.TW", available=True),
            _return_label(target="unmapped", label="unmapped", impact=0.0, available=False),
        ]
    )

    panel = build_target_day_panel(labels)

    assert len(panel) == 1
    assert panel.iloc[0]["return_target"] == "2330.TW"


def test_duplicate_key_detection_works():
    panel = pd.DataFrame(
        [
            {"taiwan_trading_date": "2026-01-15", "return_target": "2330.TW", "open_to_close_return": 0.01},
            {"taiwan_trading_date": "2026-01-15", "return_target": "2330.TW", "open_to_close_return": 0.02},
        ]
    )

    validation = validate_panel(panel)

    assert validation["duplicate_key_count"] == 1
    assert validation["warnings"]
