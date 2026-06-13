from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.regression_diagnostics import DEFAULT_DEPENDENT_VARS, run_regression_suite
from src.backtest.regression_reporting import (
    render_regression_diagnostics_report,
    save_regression_diagnostics_report,
)
from src.config import PROCESSED_DATA_DIR, REPORTS_DATA_DIR


def _label(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).date().isoformat().replace("-", "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 6C regression diagnostics.")
    parser.add_argument("--panel", required=True)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--label", default=None)
    parser.add_argument("--min-obs", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    label = _label(args.label)
    output_csv = Path(args.output_csv) if args.output_csv else PROCESSED_DATA_DIR / f"regression_results_{label}.csv"
    output_md = Path(args.output_md) if args.output_md else REPORTS_DATA_DIR / f"regression_diagnostics_{label}.md"

    panel = pd.read_csv(args.panel)
    results = run_regression_suite(panel, min_obs=args.min_obs)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_csv, index=False)
    markdown = render_regression_diagnostics_report(panel, results, report_label=label)
    saved_md = save_regression_diagnostics_report(markdown, output_md)

    fitted = int((results["status"] == "fitted").sum()) if not results.empty else 0
    insufficient = int((results["status"] == "insufficient_sample").sum()) if not results.empty else 0
    print(f"panel rows: {len(panel)}")
    print(f"dependent variables evaluated: {len(DEFAULT_DEPENDENT_VARS)}")
    print(f"models evaluated: {len(results)}")
    print(f"fitted models: {fitted}")
    print(f"insufficient-sample models: {insufficient}")
    print(f"output csv: {output_csv}")
    print(f"output markdown: {saved_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
