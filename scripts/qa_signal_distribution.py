from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


BAD_CLOUD_THEMES = {"oil / energy", "interest rates / Fed", "irrelevant"}
BAD_MATCHED_RULES = {
    "ticker:GOOGL:google",
    "sector:Cloud / Data Center:google",
}


def _split_rules(value) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def build_qa_summary(signals_df: pd.DataFrame) -> tuple[str, bool]:
    lines: list[str] = []
    if signals_df.empty:
        lines.append("No signals available.")
        return "\n".join(lines), True

    source_sector = (
        signals_df.groupby(["source", "sector"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["source", "sector"], kind="mergesort")
    )
    sector_theme = (
        signals_df.groupby(["sector", "theme"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["sector", "theme"], kind="mergesort")
    )
    suspicious = signals_df[
        (signals_df["sector"] == "Cloud / Data Center")
        & (signals_df["theme"].isin(BAD_CLOUD_THEMES))
    ]

    rule_counts: dict[str, int] = {}
    for rules in signals_df.get("matched_rules", pd.Series(dtype=str)).apply(_split_rules):
        for rule in rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
    sorted_rules = sorted(rule_counts.items(), key=lambda item: (-item[1], item[0]))

    googl_bad_count = sum(rule_counts.get(rule, 0) for rule in BAD_MATCHED_RULES)
    passed = suspicious.empty and googl_bad_count == 0

    lines.append("count by source-sector:")
    for _, row in source_sector.iterrows():
        lines.append(f"  {row['source']} | {row['sector']}: {row['count']}")

    lines.append("count by sector-theme:")
    for _, row in sector_theme.iterrows():
        lines.append(f"  {row['sector']} | {row['theme']}: {row['count']}")

    lines.append(f"suspicious Cloud/theme rows: {len(suspicious)}")
    lines.append(f"GOOGL matched-rule count: {googl_bad_count}")
    lines.append("top matched_rules:")
    for rule, count in sorted_rules[:20]:
        lines.append(f"  {rule}: {count}")

    return "\n".join(lines), passed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA rule-based signal distributions for live RSS artifacts.")
    parser.add_argument("--signals", required=True)
    parser.add_argument("--output", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    signals_df = pd.read_csv(args.signals)
    summary, passed = build_qa_summary(signals_df)
    print(summary)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
