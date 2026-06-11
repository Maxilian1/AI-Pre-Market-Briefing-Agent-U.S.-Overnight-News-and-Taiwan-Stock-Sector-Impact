"""I/O helpers for Taiwan impact candidate tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.mapping.ticker_mapper import OUTPUT_COLUMNS


def save_impact_candidates_csv(df: pd.DataFrame, output_path) -> Path:
    """Save Taiwan impact candidates with a stable column order."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [column for column in OUTPUT_COLUMNS if column in df.columns]
    extra_columns = [column for column in df.columns if column not in columns]
    df.to_csv(path, index=False, columns=columns + extra_columns)
    return path


def load_impact_candidates_csv(path) -> pd.DataFrame:
    """Load a Taiwan impact candidate CSV."""

    return pd.read_csv(path)
