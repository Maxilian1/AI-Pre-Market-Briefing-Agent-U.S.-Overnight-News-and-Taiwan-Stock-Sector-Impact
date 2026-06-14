import pandas as pd

from src.backtest.oos_validation import chronological_train_test_split
from src.config import FIXTURES_DATA_DIR


def _synthetic_oos_panel() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DATA_DIR / "sample_research_panel_oos.csv")


def test_chronological_split_uses_dates_not_random_rows():
    panel = _synthetic_oos_panel()

    train_df, test_df, metadata = chronological_train_test_split(
        panel,
        test_fraction=0.3,
        min_train_dates=20,
        min_test_dates=10,
    )

    assert metadata["split_status"] == "ok"
    train_dates = pd.to_datetime(train_df["taiwan_trading_date"])
    test_dates = pd.to_datetime(test_df["taiwan_trading_date"])
    assert train_dates.nunique() == metadata["train_date_count"]
    assert test_dates.nunique() == metadata["test_date_count"]
    assert train_dates.max() < test_dates.min()
    assert set(train_df["taiwan_trading_date"]).isdisjoint(set(test_df["taiwan_trading_date"]))


def test_chronological_split_preserves_sorted_date_order():
    panel = _synthetic_oos_panel().sample(frac=1.0, random_state=42).reset_index(drop=True)

    train_df, test_df, metadata = chronological_train_test_split(panel)

    assert metadata["split_status"] == "ok"
    assert pd.to_datetime(train_df["taiwan_trading_date"]).is_monotonic_increasing
    assert pd.to_datetime(test_df["taiwan_trading_date"]).is_monotonic_increasing


def test_insufficient_dates_return_insufficient_sample():
    panel = _synthetic_oos_panel().head(10)

    train_df, test_df, metadata = chronological_train_test_split(
        panel,
        test_fraction=0.3,
        min_train_dates=20,
        min_test_dates=10,
    )

    assert train_df.empty
    assert test_df.empty
    assert metadata["split_status"] == "insufficient_sample"
    assert "unique_dates" in metadata["notes"]
