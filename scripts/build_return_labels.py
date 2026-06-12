from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cli_utils import validate_iso_date
from src.config import PROCESSED_DATA_DIR
from src.market_data.return_labels import (
    basket_marker_to_constituents,
    build_return_labels,
    load_impact_candidates,
    save_return_labels,
)
from src.market_data.returns import (
    compute_equal_weight_basket_returns,
    compute_single_ticker_returns,
)
from src.market_data.yfinance_loader import load_price_data


def _default_output_path(date_text: str | None) -> Path:
    if date_text:
        output_date = validate_iso_date(date_text)
    else:
        output_date = datetime.now(timezone.utc).date().isoformat()
    compact_date = output_date.replace("-", "")
    return PROCESSED_DATA_DIR / f"return_labels_{compact_date}.csv"


def _compute_all_basket_returns(price_returns_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for marker, constituents in basket_marker_to_constituents().items():
        basket_returns = compute_equal_weight_basket_returns(price_returns_df, marker, constituents)
        if not basket_returns.empty:
            frames.append(basket_returns)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Phase 6A return labels for Taiwan impact candidates.")
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--prices", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--date", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        date_text = validate_iso_date(args.date)
    except ValueError as exc:
        parser.error(str(exc))

    candidates_df = load_impact_candidates(args.candidates)
    if "taiwan_trading_date" in candidates_df.columns:
        candidates_df = candidates_df[candidates_df["taiwan_trading_date"].astype(str) == date_text].copy()
    prices_df = load_price_data(args.prices)
    ticker_returns = compute_single_ticker_returns(prices_df)
    basket_returns = _compute_all_basket_returns(ticker_returns)
    labels = build_return_labels(candidates_df, ticker_returns, basket_returns)
    output_path = Path(args.output) if args.output else _default_output_path(date_text)
    saved_path = save_return_labels(labels, output_path)

    available = int(labels["return_data_available"].fillna(False).astype(bool).sum()) if not labels.empty else 0
    unavailable = int(len(labels) - available)
    print(f"input candidate rows: {len(candidates_df)}")
    print(f"return label rows: {len(labels)}")
    print(f"rows with return_data_available=True: {available}")
    print(f"rows with return_data_available=False: {unavailable}")
    print("count by taiwan_target_type:")
    if labels.empty:
        print("  none")
    else:
        counts = labels["taiwan_target_type"].fillna("").astype(str).value_counts()
        for target_type, count in counts.items():
            print(f"  {target_type or 'missing'}: {count}")
    print(f"output path: {saved_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
