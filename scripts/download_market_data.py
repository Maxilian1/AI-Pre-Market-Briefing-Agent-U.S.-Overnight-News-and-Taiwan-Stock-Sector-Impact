from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cli_utils import validate_iso_date
from src.config import FIXTURES_DATA_DIR
from src.market_data.yfinance_loader import (
    download_ohlcv,
    load_price_data,
    save_price_data,
)
from src.universe import TAIWAN_TICKERS


DEFAULT_MARKET_TICKERS = TAIWAN_TICKERS + ["QQQ", "SOXX", "SMH", "NVDA", "AMD", "TSM"]


def _parse_tickers(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_MARKET_TICKERS)
    return [part.strip() for part in value.split(",") if part.strip()]


def _filter_prices(df: pd.DataFrame, tickers: list[str], start: str, end: str) -> pd.DataFrame:
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce").dt.date.astype("string")
    working = working[
        (working["date"] >= start)
        & (working["date"] <= end)
        & (working["ticker"].astype(str).isin(tickers))
    ]
    return working.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download or load normalized daily OHLCV market data.")
    parser.add_argument("--tickers", default=None, help="Optional comma-separated ticker list.")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["fixture", "yfinance"], required=True)
    parser.add_argument("--fixture-path", default=str(FIXTURES_DATA_DIR / "sample_prices_daily.csv"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        start = validate_iso_date(args.start)
        end = validate_iso_date(args.end)
    except ValueError as exc:
        parser.error(str(exc))
    tickers = _parse_tickers(args.tickers)

    if args.mode == "fixture":
        prices = _filter_prices(load_price_data(args.fixture_path), tickers, start, end)
        missing_tickers = sorted(set(tickers) - set(prices["ticker"].dropna().astype(str)))
    else:
        prices = download_ohlcv(tickers, start, end)
        missing_tickers = list(prices.attrs.get("missing_tickers", []))

    output_path = save_price_data(prices, args.output)
    date_values = prices["date"].dropna().astype(str) if not prices.empty else pd.Series(dtype=str)
    date_range = "none"
    if not date_values.empty:
        date_range = f"{date_values.min()} to {date_values.max()}"

    print(f"total tickers: {len(tickers)}")
    print(f"rows: {len(prices)}")
    print(f"date range: {date_range}")
    print(f"missing tickers: {', '.join(missing_tickers) if missing_tickers else 'none'}")
    print(f"output path: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
