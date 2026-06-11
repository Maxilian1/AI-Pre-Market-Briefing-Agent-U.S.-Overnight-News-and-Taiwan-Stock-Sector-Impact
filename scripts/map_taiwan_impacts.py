from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DATA_DIR
from src.mapping.io import save_impact_candidates_csv
from src.mapping.ticker_mapper import load_mapping_table, map_signals_dataframe


def _default_output_path(date_text: str | None) -> Path:
    if date_text:
        output_date = date_text
    else:
        output_date = datetime.now(timezone.utc).date().isoformat()
    compact_date = output_date.replace("-", "")
    return PROCESSED_DATA_DIR / f"taiwan_impact_candidates_{compact_date}.csv"


def map_taiwan_impacts(args: argparse.Namespace) -> dict:
    signals_df = pd.read_csv(args.input)
    mapping_df = load_mapping_table(args.mapping)
    candidates_df = map_signals_dataframe(
        signals_df,
        mapping_df,
        include_irrelevant=args.include_irrelevant,
    )
    output_path = Path(args.output) if args.output else _default_output_path(args.date)
    save_impact_candidates_csv(candidates_df, output_path)

    unmapped_relevant = int(
        (candidates_df["directional_impact_label"] == "unmapped").sum()
    ) if not candidates_df.empty else 0
    target_type_counts = (
        candidates_df["taiwan_target_type"].value_counts().sort_index().to_dict()
        if not candidates_df.empty
        else {}
    )
    directional_counts = (
        candidates_df["directional_impact_label"].value_counts().sort_index().to_dict()
        if not candidates_df.empty
        else {}
    )
    top_targets = (
        candidates_df["taiwan_target"].value_counts().head(10).to_dict()
        if not candidates_df.empty
        else {}
    )

    return {
        "total_input_signals": len(signals_df),
        "total_mapped_candidate_rows": len(candidates_df),
        "unmapped_relevant_signals": unmapped_relevant,
        "count_by_taiwan_target_type": target_type_counts,
        "count_by_directional_impact_label": directional_counts,
        "top_taiwan_targets_by_candidate_count": top_targets,
        "output_path": str(output_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Map U.S. news signals to deterministic Taiwan impact candidates.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--mapping", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--include-irrelevant", action="store_true", default=False)
    return parser


def _print_counts(label: str, counts: dict) -> None:
    print(f"{label}:")
    if not counts:
        print("  none: 0")
        return
    for key, value in counts.items():
        print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = map_taiwan_impacts(args)

    print(f"total input signals: {summary['total_input_signals']}")
    print(f"total mapped candidate rows: {summary['total_mapped_candidate_rows']}")
    print(f"unmapped relevant signals: {summary['unmapped_relevant_signals']}")
    _print_counts("count by taiwan_target_type", summary["count_by_taiwan_target_type"])
    _print_counts("count by directional_impact_label", summary["count_by_directional_impact_label"])
    _print_counts("top Taiwan targets by candidate count", summary["top_taiwan_targets_by_candidate_count"])
    print(f"output path: {summary['output_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
