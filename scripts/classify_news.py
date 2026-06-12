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
from src.signals.io import save_signals_csv
from src.signals.rule_based_classifier import classify_news_dataframe


def _default_output_path(date_text: str | None) -> Path:
    if date_text:
        output_date = validate_iso_date(date_text)
    else:
        output_date = datetime.now(timezone.utc).date().isoformat()
    compact_date = output_date.replace("-", "")
    return PROCESSED_DATA_DIR / f"news_signals_{compact_date}.csv"


def classify_news(args: argparse.Namespace) -> dict:
    if args.date:
        args.date = validate_iso_date(args.date)
    raw_df = pd.read_csv(args.input)
    signal_df = classify_news_dataframe(raw_df, keep_duplicates=args.keep_duplicates)
    output_path = Path(args.output) if args.output else _default_output_path(args.date)
    save_signals_csv(signal_df, output_path)

    removed_count = len(raw_df) - len(signal_df)
    return {
        "total_raw_rows": len(raw_df),
        "total_classified_rows": len(signal_df),
        "duplicate_groups_removed": removed_count,
        "count_by_sector": signal_df["sector"].value_counts().sort_index().to_dict(),
        "count_by_sentiment_label": signal_df["sentiment_label"].value_counts().sort_index().to_dict(),
        "count_by_relevance_label": signal_df["relevance_label"].value_counts().sort_index().to_dict(),
        "output_path": str(output_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify raw news metadata into rule-based research signals.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--keep-duplicates", action="store_true", default=False)
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
    if args.date:
        try:
            args.date = validate_iso_date(args.date)
        except ValueError as exc:
            parser.error(str(exc))
    summary = classify_news(args)

    print(f"total raw rows: {summary['total_raw_rows']}")
    print(f"total classified rows: {summary['total_classified_rows']}")
    print(f"duplicate groups removed: {summary['duplicate_groups_removed']}")
    _print_counts("count by sector", summary["count_by_sector"])
    _print_counts("count by sentiment_label", summary["count_by_sentiment_label"])
    _print_counts("count by relevance_label", summary["count_by_relevance_label"])
    print(f"output path: {summary['output_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
