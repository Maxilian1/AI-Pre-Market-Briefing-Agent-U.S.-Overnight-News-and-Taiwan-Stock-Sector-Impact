from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.qa_signal_distribution import build_qa_summary


def _raw_diagnostics(raw_path: str | None) -> str:
    if not raw_path:
        return ""
    raw_df = pd.read_csv(raw_path)
    lines = [
        "raw metadata diagnostics:",
        f"  raw rows: {len(raw_df)}",
    ]
    if "duplicate_group_id" in raw_df.columns:
        groups = raw_df["duplicate_group_id"].fillna("").astype(str)
        groups = groups[groups.str.strip() != ""]
        lines.append(f"  unique duplicate groups: {groups.nunique()}")
    if "published_at_utc" in raw_df.columns:
        published = raw_df["published_at_utc"]
        missing = int((published.isna() | (published.fillna("").astype(str).str.strip() == "")).sum())
        lines.append(f"  missing published_at_utc: {missing}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA live RSS classification artifacts.")
    parser.add_argument("--signals", required=True)
    parser.add_argument("--raw", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    signals_df = pd.read_csv(args.signals)
    summary, passed = build_qa_summary(signals_df)
    print(summary)
    raw_summary = _raw_diagnostics(args.raw)
    if raw_summary:
        print(raw_summary)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
