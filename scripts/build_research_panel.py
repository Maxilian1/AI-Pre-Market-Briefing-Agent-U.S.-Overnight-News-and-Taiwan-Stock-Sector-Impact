from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest.baseline_controls import (
    align_controls_to_taiwan_dates,
    compute_control_returns,
    load_normalized_prices,
)
from src.backtest.research_panel import (
    build_target_day_panel,
    load_return_label_files,
    validate_panel,
)
from src.config import PROCESSED_DATA_DIR


def _label(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).date().isoformat().replace("-", "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Phase 6C target-day research panel.")
    parser.add_argument("--return-labels", nargs="+", required=True)
    parser.add_argument("--prices", default=None)
    parser.add_argument("--output-panel", default=None)
    parser.add_argument("--output-controls", default=None)
    parser.add_argument("--label", default=None)
    parser.add_argument("--aggregation-mode", default="target_day")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    label = _label(args.label)
    panel_path = Path(args.output_panel) if args.output_panel else PROCESSED_DATA_DIR / f"research_panel_{label}.csv"
    controls_path = Path(args.output_controls) if args.output_controls else PROCESSED_DATA_DIR / f"baseline_controls_{label}.csv"

    return_labels = load_return_label_files(args.return_labels)
    panel = build_target_day_panel(return_labels, aggregation_mode=args.aggregation_mode)
    controls_added = False
    control_returns = None
    if args.prices:
        prices = load_normalized_prices(args.prices)
        control_returns = compute_control_returns(prices)
        panel = align_controls_to_taiwan_dates(panel, control_returns)
        controls_added = True

    panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(panel_path, index=False)
    if control_returns is not None:
        controls_path.parent.mkdir(parents=True, exist_ok=True)
        control_returns.to_csv(controls_path, index=False)

    validation = validate_panel(panel)
    print(f"input rows: {len(return_labels)}")
    print(f"panel rows: {len(panel)}")
    print(f"unique dates: {validation['unique_dates']}")
    print(f"unique targets: {validation['unique_targets']}")
    print(f"duplicate key count: {validation['duplicate_key_count']}")
    print(f"controls added: {controls_added}")
    print(f"output panel: {panel_path}")
    print(f"output controls: {controls_path if control_returns is not None else 'not generated'}")
    if validation["warnings"]:
        print(f"warnings: {'; '.join(validation['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
