from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.report_generator import REQUIRED_REPORT_SECTIONS


WATCHLIST_REPEAT_THRESHOLD = 4


def _section_text(report: str, header: str) -> str:
    pattern = re.compile(rf"^## {re.escape(header)}\s*$", flags=re.MULTILINE)
    match = pattern.search(report)
    if not match:
        return ""
    next_match = re.search(r"^## .+$", report[match.end() :], flags=re.MULTILINE)
    if not next_match:
        return report[match.end() :]
    return report[match.end() : match.end() + next_match.start()]


def _watchlist_ticker_counts(report: str) -> dict[str, int]:
    watchlist = _section_text(report, "Taiwan Watchlist Candidates")
    counts: dict[str, int] = {}
    for line in watchlist.splitlines():
        if not line.startswith("- "):
            continue
        match = re.search(r"\b\d{4}\.TW\b", line)
        if match:
            ticker = match.group(0)
            counts[ticker] = counts.get(ticker, 0) + 1
    return counts


def validate_report_text(report: str) -> tuple[list[str], list[str]]:
    """Return report QA errors and warnings."""

    errors: list[str] = []
    warnings: list[str] = []
    for section in REQUIRED_REPORT_SECTIONS:
        if f"## {section}" not in report and section != "Executive Summary":
            errors.append(f"missing required section: {section}")
        elif section == "Executive Summary" and "## Executive Summary" not in report:
            errors.append("missing required section: Executive Summary")

    lowered = report.lower()
    if "restricted wording" in lowered:
        errors.append('report contains awkward token "restricted wording"')
    if "requires validation" not in lowered:
        errors.append('report missing "requires validation"')
    if "not investment advice" not in lowered:
        errors.append('report missing "not investment advice"')
    if "source provenance" not in lowered:
        errors.append("report missing Source Provenance")
    if "market context signals" not in lowered:
        errors.append("report missing Market Context Signals")

    repeated = {
        ticker: count
        for ticker, count in _watchlist_ticker_counts(report).items()
        if count > WATCHLIST_REPEAT_THRESHOLD
    }
    if repeated:
        errors.append(f"watchlist repeated ticker rows beyond threshold: {repeated}")

    if "external headline:" not in lowered:
        warnings.append("no external headline labels found")

    return errors, warnings


def build_diagnostics(signals_path: str | None = None, candidates_path: str | None = None) -> str:
    lines: list[str] = []
    if signals_path:
        signals_df = pd.read_csv(signals_path)
        lines.append("count by sector/theme:")
        if signals_df.empty:
            lines.append("  none")
        else:
            sector_theme = (
                signals_df.groupby(["sector", "theme"], dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values(["sector", "theme"], kind="mergesort")
            )
            for _, row in sector_theme.iterrows():
                lines.append(f"  {row['sector']} | {row['theme']}: {row['count']}")
            irrelevant = signals_df[signals_df["sector"] == "Irrelevant"]
            lines.append("representative irrelevant headlines:")
            for headline in irrelevant.get("title", pd.Series(dtype=str)).dropna().head(5):
                lines.append(f"  External headline: {headline}")

    if candidates_path:
        candidates_df = pd.read_csv(candidates_path)
        lines.append("top Taiwan targets:")
        if candidates_df.empty or "taiwan_target" not in candidates_df.columns:
            lines.append("  none")
        else:
            counts = candidates_df["taiwan_target"].fillna("").astype(str)
            counts = counts[counts.str.strip() != ""].value_counts().head(10)
            if counts.empty:
                lines.append("  none")
            else:
                for target, count in counts.items():
                    lines.append(f"  {target}: {count}")
        unmapped_count = 0
        if "taiwan_target_type" in candidates_df.columns:
            unmapped_count = int((candidates_df["taiwan_target_type"] == "unmapped").sum())
        lines.append(f"unmapped count: {unmapped_count}")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QA generated pre-market report output.")
    parser.add_argument("--report", required=True)
    parser.add_argument("--signals", default=None)
    parser.add_argument("--candidates", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"ERROR: report does not exist: {report_path}")
        return 1

    report = report_path.read_text(encoding="utf-8")
    errors, warnings = validate_report_text(report)
    print(f"report path: {report_path}")
    print(f"report QA errors: {len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    diagnostics = build_diagnostics(args.signals, args.candidates)
    if diagnostics:
        print(diagnostics)

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
