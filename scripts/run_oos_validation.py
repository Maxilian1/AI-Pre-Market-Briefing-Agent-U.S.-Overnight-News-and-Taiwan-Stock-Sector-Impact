from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.oos_reporting import render_oos_validation_report, save_oos_validation_report
from src.backtest.oos_validation import DEFAULT_MODEL_SPECS, compare_model_families, run_oos_validation
from src.config import PROCESSED_DATA_DIR, REPORTS_DATA_DIR


def _label(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).date().isoformat().replace("-", "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 6D chronological OOS validation diagnostics.")
    parser.add_argument("--panel", required=True)
    parser.add_argument("--label", default=None)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--test-fraction", type=float, default=0.3)
    parser.add_argument("--min-train-dates", type=int, default=20)
    parser.add_argument("--min-test-dates", type=int, default=10)
    parser.add_argument(
        "--data-mode",
        choices=["fixture", "live", "synthetic", "unknown"],
        default="unknown",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    label = _label(args.label)
    output_csv = Path(args.output_csv) if args.output_csv else PROCESSED_DATA_DIR / f"oos_validation_results_{label}.csv"
    output_md = Path(args.output_md) if args.output_md else REPORTS_DATA_DIR / f"oos_validation_summary_{label}.md"

    panel = pd.read_csv(args.panel)
    results = run_oos_validation(
        panel,
        test_fraction=args.test_fraction,
        min_train_dates=args.min_train_dates,
        min_test_dates=args.min_test_dates,
    )
    comparison = compare_model_families(results)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_csv, index=False)
    markdown = render_oos_validation_report(
        panel,
        results,
        comparison,
        report_label=label,
        data_mode=args.data_mode,
    )
    saved_md = save_oos_validation_report(markdown, output_md)

    unique_dates = int(panel["taiwan_trading_date"].nunique()) if "taiwan_trading_date" in panel.columns else 0
    fitted = int((results["status"] == "fitted").sum()) if not results.empty else 0
    insufficient = int((results["status"] == "insufficient_sample").sum()) if not results.empty else 0
    status_values = ",".join(sorted(results["status"].dropna().unique())) if not results.empty else "none"
    print(f"panel rows: {len(panel)}")
    print(f"unique dates: {unique_dates}")
    print(f"model families evaluated: {len(DEFAULT_MODEL_SPECS)}")
    print(f"fitted validations: {fitted}")
    print(f"insufficient-sample validations: {insufficient}")
    print(f"status values: {status_values}")
    print(f"output csv: {output_csv}")
    print(f"output markdown: {saved_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
