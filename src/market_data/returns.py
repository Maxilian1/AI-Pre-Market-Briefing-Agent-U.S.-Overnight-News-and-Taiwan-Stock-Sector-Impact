"""Return calculations for Phase 6A market outcome labels."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


RETURN_COLUMNS = [
    "date",
    "return_target",
    "return_target_type",
    "open_price",
    "close_price",
    "previous_close_price",
    "next_close_price",
    "prev_close_to_open_return",
    "open_to_close_return",
    "close_to_close_return",
    "next_close_to_close_return",
    "return_data_available",
    "return_data_notes",
]


def _to_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.mask(denominator == 0)
    return numerator / denominator - 1


def _availability(row: pd.Series) -> bool:
    required = [
        "open_price",
        "close_price",
        "previous_close_price",
        "next_close_price",
        "prev_close_to_open_return",
        "open_to_close_return",
        "close_to_close_return",
        "next_close_to_close_return",
    ]
    return all(pd.notna(row.get(column)) for column in required)


def _clean_constituents(constituents: Iterable[str]) -> list[str]:
    return [str(ticker).strip() for ticker in constituents if str(ticker).strip()]


def compute_single_ticker_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily return labels for each ticker.

    Previous and next closes are aligned by the trading rows present for each
    ticker, not by calendar-day assumptions.
    """

    if price_df.empty:
        return pd.DataFrame(columns=RETURN_COLUMNS)

    required = {"date", "ticker", "open", "close"}
    missing = required - set(price_df.columns)
    if missing:
        raise ValueError(f"price_df missing required columns: {sorted(missing)}")

    working = price_df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce").dt.date.astype("string")
    working["ticker"] = working["ticker"].astype(str).str.strip()
    working["open_price"] = _to_float_series(working["open"])
    working["close_price"] = _to_float_series(working["close"])
    working = working.dropna(subset=["date"])
    working = working.sort_values(["ticker", "date"], kind="mergesort")

    grouped = working.groupby("ticker", sort=False)
    working["previous_close_price"] = grouped["close_price"].shift(1)
    working["next_close_price"] = grouped["close_price"].shift(-1)
    working["prev_close_to_open_return"] = _safe_divide(
        working["open_price"],
        working["previous_close_price"],
    )
    working["open_to_close_return"] = _safe_divide(
        working["close_price"],
        working["open_price"],
    )
    working["close_to_close_return"] = _safe_divide(
        working["close_price"],
        working["previous_close_price"],
    )
    working["next_close_to_close_return"] = _safe_divide(
        working["next_close_price"],
        working["close_price"],
    )
    working["return_target"] = working["ticker"]
    working["return_target_type"] = "ticker"
    working["return_data_available"] = working.apply(_availability, axis=1)
    working["return_data_notes"] = working["return_data_available"].map(
        {
            True: "ticker return labels computed from normalized OHLCV.",
            False: "ticker price row is missing previous, current, or next trading-day data.",
        }
    )

    return working[RETURN_COLUMNS].reset_index(drop=True)


def compute_equal_weight_basket_returns(
    price_returns_df: pd.DataFrame,
    basket_name: str,
    constituents: list[str],
) -> pd.DataFrame:
    """Compute equal-weight basket return labels from constituent returns."""

    cleaned_constituents = _clean_constituents(constituents)
    if price_returns_df.empty or not cleaned_constituents:
        return pd.DataFrame(columns=RETURN_COLUMNS)

    working = price_returns_df[price_returns_df["return_target"].isin(cleaned_constituents)].copy()
    if working.empty:
        return pd.DataFrame(columns=RETURN_COLUMNS)

    return_metrics = [
        "prev_close_to_open_return",
        "open_to_close_return",
        "close_to_close_return",
        "next_close_to_close_return",
    ]
    rows: list[dict] = []
    for date_value, group in working.groupby("date", sort=True):
        available_targets = sorted(set(group["return_target"].dropna().astype(str)))
        missing_targets = sorted(set(cleaned_constituents) - set(available_targets))
        metric_values = {metric: group[metric].mean(skipna=True) for metric in return_metrics}
        return_data_available = bool(available_targets) and all(pd.notna(metric_values[metric]) for metric in return_metrics)
        notes = (
            "equal-weight basket return labels computed from available constituents; "
            f"used_constituents={','.join(available_targets) or 'none'}"
        )
        if missing_targets:
            notes += f"; missing_constituents={','.join(missing_targets)}"
        rows.append(
            {
                "date": str(date_value),
                "return_target": basket_name,
                "return_target_type": "basket",
                "open_price": pd.NA,
                "close_price": pd.NA,
                "previous_close_price": pd.NA,
                "next_close_price": pd.NA,
                **metric_values,
                "return_data_available": return_data_available,
                "return_data_notes": notes,
            }
        )

    return pd.DataFrame(rows, columns=RETURN_COLUMNS)


def build_return_lookup(
    price_returns_df: pd.DataFrame,
    basket_returns_df: pd.DataFrame | None = None,
) -> dict[tuple[str, str], dict]:
    """Build a lookup keyed by (return_target, date)."""

    frames = [df for df in [price_returns_df, basket_returns_df] if df is not None and not df.empty]
    if not frames:
        return {}
    combined = pd.concat(frames, ignore_index=True)
    lookup: dict[tuple[str, str], dict] = {}
    for _, row in combined.iterrows():
        target = str(row.get("return_target", "")).strip()
        date_value = str(row.get("date", "")).strip()
        if target and date_value:
            lookup[(target, date_value)] = row.to_dict()
    return lookup
