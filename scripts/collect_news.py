from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cli_utils import validate_iso_date
from src.config import FIXTURES_DATA_DIR, RAW_DATA_DIR
from src.news_collectors.dedupe import assign_duplicate_group_ids
from src.news_collectors.io import load_fixture_news, save_news_csv
from src.news_collectors.rss_collector import collect_from_feeds


def _default_output_path(date_text: str | None) -> Path:
    if date_text:
        output_date = validate_iso_date(date_text)
    else:
        output_date = datetime.now(timezone.utc).date().isoformat()
    compact_date = output_date.replace("-", "")
    return RAW_DATA_DIR / f"news_{compact_date}.csv"


def _load_feed_config(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as json_file:
        feeds = json.load(json_file)
    if not isinstance(feeds, list):
        raise ValueError("RSS feed config must contain a JSON list.")
    for feed in feeds:
        if "source" not in feed or "url" not in feed:
            raise ValueError("Each RSS feed config must include 'source' and 'url'.")
    return feeds


def collect_news(args: argparse.Namespace) -> dict[str, str | int]:
    if args.date:
        args.date = validate_iso_date(args.date)
    if args.mode == "fixture":
        fixture_path = Path(args.fixture_path or FIXTURES_DATA_DIR / "sample_raw_news.json")
        items = load_fixture_news(fixture_path)
    elif args.mode == "rss":
        if not args.feed_config:
            raise ValueError("--feed-config is required when --mode rss")
        feeds = _load_feed_config(Path(args.feed_config))
        items = collect_from_feeds(feeds)
    else:
        raise ValueError(f"Unsupported mode: {args.mode}")

    rows = assign_duplicate_group_ids(items)
    output_path = Path(args.output) if args.output else _default_output_path(args.date)
    save_news_csv(rows, output_path)

    duplicate_group_ids = {row["duplicate_group_id"] for row in rows}
    missing_published_count = sum(1 for row in rows if not row.get("published_at_utc"))

    return {
        "total_rows": len(rows),
        "unique_duplicate_groups": len(duplicate_group_ids),
        "missing_published_at_utc": missing_published_count,
        "output_path": str(output_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect raw news metadata for research fixtures or RSS feeds.")
    parser.add_argument("--mode", choices=["fixture", "rss"], required=True)
    parser.add_argument("--fixture-path", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--feed-config", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.date:
        try:
            args.date = validate_iso_date(args.date)
        except ValueError as exc:
            parser.error(str(exc))
    summary = collect_news(args)

    print(f"total rows: {summary['total_rows']}")
    print(f"unique duplicate groups: {summary['unique_duplicate_groups']}")
    print(f"missing published_at_utc: {summary['missing_published_at_utc']}")
    print(f"output path: {summary['output_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
