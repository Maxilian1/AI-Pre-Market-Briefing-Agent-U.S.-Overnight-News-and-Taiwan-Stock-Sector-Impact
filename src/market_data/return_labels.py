"""Join Taiwan impact candidates to Phase 6A market return labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.market_data.returns import RETURN_COLUMNS, build_return_lookup
from src.universe import BASKETS


BASKET_MARKER_TO_UNIVERSE_NAME = {
    "BASKET:TW_SEMICONDUCTOR": "Taiwan Semiconductor Basket",
    "BASKET:TW_AI_SERVER": "Taiwan AI Server Basket",
    "BASKET:TW_APPLE_SUPPLY_CHAIN": "Taiwan Apple Supply Chain Basket",
    "BASKET:TW_POWER_DATA_CENTER": "Taiwan Power / Data Center Basket",
}
UNIVERSE_NAME_TO_BASKET_MARKER = {
    universe_name: marker
    for marker, universe_name in BASKET_MARKER_TO_UNIVERSE_NAME.items()
}

REQUIRED_RETURN_LABEL_COLUMNS = [
    "taiwan_trading_date",
    "taiwan_target",
    "taiwan_target_type",
    "taiwan_ticker",
    "taiwan_company",
    "taiwan_sector",
    "directional_impact_label",
    "impact_score",
    "combined_confidence",
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


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def load_impact_candidates(path) -> pd.DataFrame:
    """Load Taiwan impact candidates from CSV."""

    return pd.read_csv(path)


def basket_marker_to_constituents() -> dict[str, list[str]]:
    """Return Phase 6A basket marker to constituent ticker mapping."""

    return {
        marker: list(BASKETS[universe_name])
        for marker, universe_name in BASKET_MARKER_TO_UNIVERSE_NAME.items()
    }


def _candidate_return_target(row: pd.Series) -> tuple[str, str, str]:
    target_type = _clean_text(row.get("taiwan_target_type"))
    taiwan_ticker = _clean_text(row.get("taiwan_ticker"))
    taiwan_target = _clean_text(row.get("taiwan_target"))

    if target_type == "ticker" and taiwan_ticker:
        return taiwan_ticker, "ticker", ""
    if target_type == "basket":
        marker = taiwan_ticker if taiwan_ticker.startswith("BASKET:") else taiwan_target
        if marker in UNIVERSE_NAME_TO_BASKET_MARKER:
            marker = UNIVERSE_NAME_TO_BASKET_MARKER[marker]
        if marker in BASKET_MARKER_TO_UNIVERSE_NAME:
            return marker, "basket", ""
        return marker or taiwan_target, "basket", "basket marker is not recognized in Phase 6A."
    if target_type == "proxy":
        return taiwan_ticker or taiwan_target or "proxy", "proxy", "proxy rows do not receive Taiwan return labels in Phase 6A."
    return taiwan_ticker or taiwan_target or "unmapped", "unmapped", "unmapped rows do not receive Taiwan return labels in Phase 6A."


def _empty_return_payload(target: str, target_type: str, note: str) -> dict:
    payload = {column: pd.NA for column in RETURN_COLUMNS}
    payload.update(
        {
            "return_target": target,
            "return_target_type": target_type,
            "return_data_available": False,
            "return_data_notes": note,
        }
    )
    return payload


def _candidate_metadata(row: pd.Series) -> dict:
    return {
        "taiwan_trading_date": _clean_text(row.get("taiwan_trading_date")),
        "taiwan_target": _clean_text(row.get("taiwan_target")),
        "taiwan_target_type": _clean_text(row.get("taiwan_target_type")),
        "taiwan_ticker": _clean_text(row.get("taiwan_ticker")),
        "taiwan_company": _clean_text(row.get("taiwan_company")),
        "taiwan_sector": _clean_text(row.get("taiwan_sector")),
        "directional_impact_label": _clean_text(row.get("directional_impact_label")),
        "impact_score": _to_float(row.get("impact_score")),
        "combined_confidence": _to_float(row.get("combined_confidence")),
    }


def build_return_labels(
    candidates_df: pd.DataFrame,
    price_returns_df: pd.DataFrame,
    basket_returns_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build return label rows for every Taiwan impact candidate row."""

    lookup = build_return_lookup(price_returns_df, basket_returns_df)
    rows: list[dict] = []
    for _, candidate in candidates_df.iterrows():
        metadata = _candidate_metadata(candidate)
        target, target_type, skip_note = _candidate_return_target(candidate)
        trading_date = metadata["taiwan_trading_date"]

        if skip_note:
            return_payload = _empty_return_payload(target, target_type, skip_note)
        else:
            matched = lookup.get((target, trading_date))
            if matched is None:
                return_payload = _empty_return_payload(
                    target,
                    target_type,
                    "missing price return labels for target/date.",
                )
            else:
                return_payload = {column: matched.get(column, pd.NA) for column in RETURN_COLUMNS}
                return_payload["return_target"] = target
                return_payload["return_target_type"] = target_type
                if not bool(return_payload.get("return_data_available")):
                    note = _clean_text(return_payload.get("return_data_notes"))
                    return_payload["return_data_notes"] = note or "price return labels are incomplete for target/date."

        rows.append({**metadata, **return_payload})

    return pd.DataFrame(rows, columns=REQUIRED_RETURN_LABEL_COLUMNS)


def save_return_labels(df: pd.DataFrame, output_path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path)
