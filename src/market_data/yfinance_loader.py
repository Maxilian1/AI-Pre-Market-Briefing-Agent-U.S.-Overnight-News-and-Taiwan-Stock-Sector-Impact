"""Market data loading helpers for Phase 6A return labels."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


NORMALIZED_PRICE_COLUMNS = [
    "date",
    "ticker",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
]


def _clean_tickers(tickers: Iterable[str]) -> list[str]:
    return [str(ticker).strip() for ticker in tickers if str(ticker).strip()]


def _empty_price_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=NORMALIZED_PRICE_COLUMNS)


def _normalize_plain_yfinance_output(raw_df: pd.DataFrame, ticker: str | None = None) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return _empty_price_frame()

    working = raw_df.copy()
    if isinstance(working.index, pd.DatetimeIndex) or working.index.name:
        working = working.reset_index()

    rename_map = {
        "Date": "date",
        "Datetime": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Adj_Close": "adj_close",
        "Volume": "volume",
        "Ticker": "ticker",
    }
    working = working.rename(columns=rename_map)
    working.columns = [str(column).strip().lower().replace(" ", "_") for column in working.columns]
    if "date" not in working.columns and "index" in working.columns:
        working = working.rename(columns={"index": "date"})
    if "ticker" not in working.columns:
        working["ticker"] = ticker or ""
    if "adj_close" not in working.columns and "close" in working.columns:
        working["adj_close"] = working["close"]

    for column in NORMALIZED_PRICE_COLUMNS:
        if column not in working.columns:
            working[column] = pd.NA

    working["date"] = pd.to_datetime(working["date"], errors="coerce").dt.date.astype("string")
    working["ticker"] = working["ticker"].astype(str).str.strip()
    for column in ["open", "high", "low", "close", "adj_close", "volume"]:
        working[column] = pd.to_numeric(working[column], errors="coerce")

    working = working[NORMALIZED_PRICE_COLUMNS]
    working = working.dropna(subset=["date"])
    return working.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)


def normalize_yfinance_output(raw_df) -> pd.DataFrame:
    """Normalize yfinance output to one row per date and ticker.

    Supports both the plain single-ticker yfinance frame and common MultiIndex
    layouts. The returned columns are stable for downstream tests and scripts.
    """

    if raw_df is None or len(raw_df) == 0:
        return _empty_price_frame()

    if isinstance(raw_df.columns, pd.MultiIndex):
        frames: list[pd.DataFrame] = []
        level_zero = list(raw_df.columns.get_level_values(0).unique())
        level_one = list(raw_df.columns.get_level_values(1).unique())
        price_fields = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}

        if price_fields.intersection(set(str(value) for value in level_one)):
            for ticker in level_zero:
                sub_df = raw_df[ticker].copy()
                normalized = _normalize_plain_yfinance_output(sub_df, ticker=str(ticker))
                if not normalized.empty:
                    frames.append(normalized)
        else:
            for ticker in level_one:
                sub_df = raw_df.xs(ticker, axis=1, level=1).copy()
                normalized = _normalize_plain_yfinance_output(sub_df, ticker=str(ticker))
                if not normalized.empty:
                    frames.append(normalized)
        if not frames:
            return _empty_price_frame()
        return pd.concat(frames, ignore_index=True)[NORMALIZED_PRICE_COLUMNS]

    return _normalize_plain_yfinance_output(pd.DataFrame(raw_df))


def download_ohlcv(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download daily OHLCV rows from yfinance for manual/live use.

    Tests should not call this function. Failed individual tickers are recorded
    in ``df.attrs["missing_tickers"]``; a RuntimeError is raised only when all
    requested tickers fail or return no rows.
    """

    cleaned_tickers = _clean_tickers(tickers)
    if not cleaned_tickers:
        raise ValueError("At least one ticker is required.")

    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required for --mode yfinance.") from exc

    frames: list[pd.DataFrame] = []
    missing_tickers: list[str] = []
    for ticker in cleaned_tickers:
        try:
            raw_df = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception:
            missing_tickers.append(ticker)
            continue

        normalized = normalize_yfinance_output(raw_df)
        if normalized.empty:
            missing_tickers.append(ticker)
        else:
            if set(normalized["ticker"].fillna("").astype(str).str.strip()) <= {""}:
                normalized["ticker"] = ticker
            frames.append(normalized)

    if not frames:
        raise RuntimeError("No OHLCV rows were downloaded for any requested ticker.")

    result = pd.concat(frames, ignore_index=True)[NORMALIZED_PRICE_COLUMNS]
    result = result.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)
    result.attrs["missing_tickers"] = missing_tickers
    return result


def save_price_data(df: pd.DataFrame, output_path) -> str:
    """Save normalized price data to CSV."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path)


def load_price_data(path) -> pd.DataFrame:
    """Load normalized price data from CSV."""

    df = pd.read_csv(path)
    for column in NORMALIZED_PRICE_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    return df[NORMALIZED_PRICE_COLUMNS].copy()
