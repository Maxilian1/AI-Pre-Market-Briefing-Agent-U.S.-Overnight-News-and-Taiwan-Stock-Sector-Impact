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
from src.config import REPORTS_DATA_DIR
from src.reporting.report_generator import (
    generate_report,
    load_report_inputs,
    summarize_candidates,
    summarize_themes,
)


def _default_output_path(date_text: str | None) -> Path:
    if date_text:
        output_date = validate_iso_date(date_text)
    else:
        output_date = datetime.now(timezone.utc).date().isoformat()
    compact_date = output_date.replace("-", "")
    return REPORTS_DATA_DIR / f"taiwan_premarket_report_{compact_date}.md"


def _top_themes(theme_summary: list[dict], limit: int = 5) -> str:
    if not theme_summary:
        return "none"
    return ", ".join(
        f"{row['sector']} / {row['theme']} ({row['signal_count']})"
        for row in theme_summary[:limit]
    )


def _top_targets(candidates_df: pd.DataFrame, limit: int = 5) -> str:
    if candidates_df.empty or "taiwan_target" not in candidates_df.columns:
        return "none"
    counts = candidates_df["taiwan_target"].fillna("").astype(str)
    counts = counts[counts.str.strip() != ""].value_counts().head(limit)
    if counts.empty:
        return "none"
    return ", ".join(f"{target} ({count})" for target, count in counts.items())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a deterministic Taiwan pre-market research brief.")
    parser.add_argument("--signals", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--output", default=None)
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
    signals_df, candidates_df = load_report_inputs(args.signals, args.candidates)
    output_path = Path(args.output) if args.output else _default_output_path(args.date)
    saved_path = generate_report(args.signals, args.candidates, output_path, report_date=args.date)

    print(f"report date: {args.date or 'unspecified'}")
    print(f"number of input signals: {len(signals_df)}")
    print(f"number of impact candidates: {len(candidates_df)}")
    print(f"top 5 themes: {_top_themes(summarize_themes(signals_df))}")
    print(f"top 5 Taiwan targets: {_top_targets(summarize_candidates(candidates_df))}")
    print(f"output path: {saved_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
