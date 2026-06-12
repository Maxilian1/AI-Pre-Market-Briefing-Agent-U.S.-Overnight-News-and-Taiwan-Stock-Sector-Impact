from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.event_study import load_return_labels, run_event_study
from src.backtest.reporting import render_event_study_summary, save_event_study_summary
from src.cli_utils import validate_iso_date
from src.config import PROCESSED_DATA_DIR, REPORTS_DATA_DIR


def _compact_date(date_text: str | None) -> str:
    if date_text:
        return validate_iso_date(date_text).replace("-", "")
    return datetime.now(timezone.utc).date().isoformat().replace("-", "")


def _default_paths(date_text: str | None) -> tuple[Path, Path, Path]:
    compact = _compact_date(date_text)
    return (
        PROCESSED_DATA_DIR / f"event_study_results_{compact}.csv",
        PROCESSED_DATA_DIR / f"event_study_aggregated_{compact}.csv",
        REPORTS_DATA_DIR / f"event_study_summary_{compact}.md",
    )


def _results_table(study_results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bucket = study_results["bucket_summary"].copy()
    hit = study_results["directional_hit_ratio"].copy()
    if bucket.empty:
        return bucket
    if hit.empty:
        bucket["directional_hit_count"] = pd.NA
        bucket["directional_hit_ratio"] = pd.NA
        bucket["directional_hit_rule"] = ""
        return bucket
    hit = hit.rename(
        columns={
            "n": "directional_n",
            "hit_count": "directional_hit_count",
            "hit_ratio": "directional_hit_ratio",
            "hit_rule": "directional_hit_rule",
        }
    )
    return bucket.merge(
        hit[
            [
                "return_col",
                "final_directional_label",
                "directional_n",
                "directional_hit_count",
                "directional_hit_ratio",
                "directional_hit_rule",
            ]
        ],
        on=["return_col", "final_directional_label"],
        how="left",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 6B event-study diagnostics for return labels.")
    parser.add_argument("--return-labels", nargs="+", required=True)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-aggregated", default=None)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--date", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.date:
        try:
            args.date = validate_iso_date(args.date)
        except ValueError as exc:
            parser.error(str(exc))

    default_csv, default_aggregated, default_md = _default_paths(args.date)
    output_csv = Path(args.output_csv) if args.output_csv else default_csv
    output_aggregated = Path(args.output_aggregated) if args.output_aggregated else default_aggregated
    output_md = Path(args.output_md) if args.output_md else default_md

    return_labels = load_return_labels(args.return_labels)
    study_results = run_event_study(return_labels)
    aggregated = study_results["aggregated"]
    results = _results_table(study_results)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_aggregated.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_csv, index=False)
    aggregated.to_csv(output_aggregated, index=False)
    markdown = render_event_study_summary(
        return_labels,
        aggregated,
        study_results["bucket_summary"],
        study_results["directional_hit_ratio"],
        report_date=args.date,
    )
    saved_md = save_event_study_summary(markdown, output_md)

    available = int(aggregated["return_data_available"].fillna(False).astype(bool).sum()) if not aggregated.empty else 0
    unavailable = int(len(aggregated) - available)
    print(f"input rows: {len(return_labels)}")
    print(f"aggregated rows: {len(aggregated)}")
    print(f"rows with available returns: {available}")
    print(f"rows without available returns: {unavailable}")
    print("count by final_directional_label:")
    if aggregated.empty:
        print("  none")
    else:
        counts = aggregated["final_directional_label"].fillna("").astype(str).value_counts()
        for label, count in counts.items():
            print(f"  {label or 'missing'}: {count}")
    print(f"output csv: {output_csv}")
    print(f"output aggregated: {output_aggregated}")
    print(f"output markdown: {saved_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
