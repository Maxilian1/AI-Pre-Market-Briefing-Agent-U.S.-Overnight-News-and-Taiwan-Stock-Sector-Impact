"""Baseline-control return construction and alignment for Phase 6C."""

from __future__ import annotations

from bisect import bisect_left

import pandas as pd

from src.market_data.returns import compute_single_ticker_returns
from src.market_data.yfinance_loader import load_price_data


CONTROL_TICKER_COLUMNS = {
    "QQQ": "qqq_return",
    "SOXX": "soxx_return",
    "SMH": "smh_return",
    "NVDA": "nvda_return",
    "AMD": "amd_return",
    "TSM": "tsm_adr_return",
}


def load_normalized_prices(path) -> pd.DataFrame:
    """Load normalized daily price data."""

    return load_price_data(path)


def compute_control_returns(price_df: pd.DataFrame, control_tickers: dict[str, str] | None = None) -> pd.DataFrame:
    """Compute wide U.S. control close-to-close returns."""

    ticker_map = dict(control_tickers or CONTROL_TICKER_COLUMNS)
    if price_df.empty:
        df = pd.DataFrame(columns=["us_trading_date", *ticker_map.values(), "control_data_notes"])
        df.attrs["warnings"] = ["price data is empty"]
        return df

    ticker_returns = compute_single_ticker_returns(price_df)
    dates = sorted(ticker_returns["date"].dropna().astype(str).unique())
    controls = pd.DataFrame({"us_trading_date": dates})
    warnings: list[str] = []
    for ticker, column in ticker_map.items():
        ticker_df = ticker_returns[ticker_returns["return_target"] == ticker][["date", "close_to_close_return"]].copy()
        if ticker_df.empty:
            controls[column] = pd.NA
            warnings.append(f"missing control ticker: {ticker}")
            continue
        ticker_df = ticker_df.rename(columns={"date": "us_trading_date", "close_to_close_return": column})
        controls = controls.merge(ticker_df, on="us_trading_date", how="left")

    controls["control_data_notes"] = ""
    if warnings:
        controls["control_data_notes"] = "; ".join(warnings)
    controls.attrs["warnings"] = warnings
    return controls.sort_values("us_trading_date", kind="mergesort").reset_index(drop=True)


def _previous_control_date(taiwan_date: str, control_dates: list[str]) -> str | None:
    index = bisect_left(control_dates, taiwan_date) - 1
    if index < 0:
        return None
    return control_dates[index]


def align_controls_to_taiwan_dates(panel_df: pd.DataFrame, control_returns_df: pd.DataFrame) -> pd.DataFrame:
    """Align U.S. control returns to each Taiwan date using the prior U.S. trading date."""

    panel = panel_df.copy()
    control_columns = [column for column in CONTROL_TICKER_COLUMNS.values() if column in control_returns_df.columns]
    for column in CONTROL_TICKER_COLUMNS.values():
        if column not in panel.columns:
            panel[column] = pd.NA
    panel["us_control_date"] = pd.NA
    panel["control_data_notes"] = ""

    if control_returns_df.empty or "us_trading_date" not in control_returns_df.columns:
        panel["control_data_notes"] = "no control return data available."
        return panel

    controls = control_returns_df.copy()
    controls["us_trading_date"] = controls["us_trading_date"].astype(str)
    control_dates = sorted(controls["us_trading_date"].dropna().unique())
    controls_by_date = {
        str(row["us_trading_date"]): row.to_dict()
        for _, row in controls.iterrows()
    }

    aligned_rows = []
    for _, row in panel.iterrows():
        row_dict = row.to_dict()
        taiwan_date = str(row_dict.get("taiwan_trading_date", ""))
        control_date = _previous_control_date(taiwan_date, control_dates)
        if control_date is None:
            row_dict["control_data_notes"] = "no prior U.S. control trading date available."
        else:
            control_row = controls_by_date[control_date]
            row_dict["us_control_date"] = control_date
            notes = str(control_row.get("control_data_notes", "") or "")
            row_dict["control_data_notes"] = notes
            for column in control_columns:
                row_dict[column] = control_row.get(column, pd.NA)
        aligned_rows.append(row_dict)

    return pd.DataFrame(aligned_rows)
