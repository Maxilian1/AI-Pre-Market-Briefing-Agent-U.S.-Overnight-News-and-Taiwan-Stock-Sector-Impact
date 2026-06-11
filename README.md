# AI Pre-Market Briefing Agent

This repository is a quantitative finance research project for studying whether overnight U.S. semiconductor / AI financial news signals have explanatory power for Taiwan semiconductor and AI supply-chain stock returns before the TWSE opens.

Core research question:

Can overnight U.S. semiconductor / AI financial news signals provide incremental explanatory power for Taiwan semiconductor and AI supply-chain returns before TWSE opens?

This is not a stock recommendation app. The project stores structured research signals, controls, and backtest outputs for validation. It must not produce buy, sell, or guaranteed-return recommendations.

## Phase 1 Status

Phase 1 creates the reproducible scaffold only:

- Project directories for raw data, processed data, fixtures, reports, source code, scripts, tests, and notebooks.
- Static U.S. and Taiwan ticker universes for the initial semiconductor / AI supply-chain scope.
- Seed Taiwan basket definitions.
- A transparent seed ticker mapping CSV with assumption flags.
- Timezone utilities for UTC and Asia/Taipei timestamp handling.
- Smoke tests for universe integrity, timestamp assignment, and seed mapping structure.

Phase 1 does not collect news, call external APIs, scrape websites, ingest market data, create signals, or run backtests.

## Phase 2 Status

Phase 2 adds the raw news metadata collection layer:

- `NewsItem` schema for metadata-only records.
- Deterministic URL/title hashing and duplicate grouping.
- Fixture-driven raw news loading for reproducible tests.
- Lightweight RSS metadata collection using feedparser.
- CSV output for raw news rows.

Phase 2 still does not implement LLM classification, sentiment scoring, Taiwan ticker mapping from news, market data ingestion, backtesting, full article scraping, paywalled scraping, or trading recommendations.

## Project Structure

```text
data/
  raw/
  processed/
  fixtures/
  reports/
src/
  config.py
  universe.py
  time_utils.py
  news_collectors/
  market_data/
  mapping/
  signals/
  backtest/
  reporting/
scripts/
tests/
notebooks/
```

## Basic Commands

Run tests:

```powershell
python -m pytest
```

Run a basic import check:

```powershell
python -c "from src import universe, time_utils; print('import ok')"
```

Collect fixture news metadata:

```powershell
python scripts/collect_news.py --mode fixture --date 2026-01-15
```

Run the Phase 2 news import check:

```powershell
python -c "from src.news_collectors.base import NewsItem; print('news import ok')"
```

Fixture mode is reproducible and uses synthetic sample metadata from `data/fixtures/sample_raw_news.json`. RSS mode is live and may depend on network and source availability:

```powershell
python scripts/collect_news.py --mode rss --feed-config data/fixtures/rss_feeds_example.json --date 2026-01-15
```

RSS mode stores feed-provided metadata and snippets only. It does not fetch full article bodies or scrape article pages.

## Research Guardrails

- Use public, reproducible data sources only.
- Do not scrape paywalled article bodies.
- Store publication timestamps and retrieval timestamps separately.
- Preserve ticker mapping assumptions rather than inventing relationships.
- Validate any signal claims through backtests before interpreting results.
- Use cautious research language such as potentially positive, potentially negative, watchlist, confidence level, possible impact, and requires validation.
