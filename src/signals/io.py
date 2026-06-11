"""I/O helpers for structured news signal tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.signals.rule_based_classifier import OUTPUT_COLUMNS


def save_signals_csv(df: pd.DataFrame, output_path) -> Path:
    """Save classified news signals with a stable column order."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [column for column in OUTPUT_COLUMNS if column in df.columns]
    extra_columns = [column for column in df.columns if column not in columns]
    df.to_csv(path, index=False, columns=columns + extra_columns)
    return path


def load_signals_csv(path) -> pd.DataFrame:
    """Load a classified news signal CSV."""

    return pd.read_csv(path)
