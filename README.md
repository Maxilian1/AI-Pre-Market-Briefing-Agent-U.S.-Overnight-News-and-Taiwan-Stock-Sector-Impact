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

## Phase 3 Status

Phase 3 adds deterministic rule-based classification from raw news metadata into a structured research feature table:

- U.S. ticker keyword matching for the initial semiconductor / AI / hardware universe.
- Sector and theme labels for semiconductor, AI infrastructure, memory, Apple supply chain, cloud/data center, macro, energy, and irrelevant items.
- Simple rule-based sentiment labels and bounded scores.
- Relevance labels and confidence scores for research filtering.
- Default duplicate suppression by `duplicate_group_id` to avoid duplicated signal inflation.

Phase 3 uses transparent rules, not LLMs. It does not infer Taiwan tickers, generate Taiwan impact reports, ingest market data, run backtests, or make trading recommendations.

## Phase 4 Status

Phase 4 adds deterministic Taiwan impact candidate mapping from structured U.S. news signals:

- Uses only `data/processed/ticker_mapping_seed.csv`.
- Maps matched U.S. tickers to seed Taiwan tickers, basket markers, or proxy markers.
- Creates explicit `unmapped` rows for relevant signals with no deterministic seed relationship.
- Computes bounded impact and confidence fields for research filtering.

Phase 4 does not collect live news, call LLM APIs, ingest market data, run backtests, generate full pre-market reports, or make trading recommendations. Output rows are potential research candidates requiring validation.

## Phase 5 Status

Phase 5 adds deterministic Markdown research reporting:

- Loads classified U.S. news signals and Taiwan impact candidates.
- Summarizes overnight U.S. themes, Taiwan watchlist candidates, directional labels, confidence, limitations, and source provenance.
- Uses deterministic tables and formatting only.
- Saves reports under `data/reports/`.

Phase 5 is not LLM-written, is not a trading recommendation system, and still requires market validation.

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

Classify fixture news metadata into research features:

```powershell
python scripts/classify_news.py --input data/raw/news_20260115.csv --date 2026-01-15
```

Map classified signals to Taiwan impact candidates:

```powershell
python scripts/map_taiwan_impacts.py --input data/processed/news_signals_20260115.csv --date 2026-01-15
```

Phase 4 PowerShell examples using a project virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts\collect_news.py --mode fixture --date 2026-01-15
.\.venv\Scripts\python.exe scripts\classify_news.py --input data\raw\news_20260115.csv --date 2026-01-15
.\.venv\Scripts\python.exe scripts\map_taiwan_impacts.py --input data\processed\news_signals_20260115.csv --date 2026-01-15
.\.venv\Scripts\python.exe -m pytest
```

Phase 5 PowerShell examples using a project virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts\collect_news.py --mode fixture --date 2026-01-15
.\.venv\Scripts\python.exe scripts\classify_news.py --input data\raw\news_20260115.csv --date 2026-01-15
.\.venv\Scripts\python.exe scripts\map_taiwan_impacts.py --input data\processed\news_signals_20260115.csv --date 2026-01-15
.\.venv\Scripts\python.exe scripts\generate_report.py --signals data\processed\news_signals_20260115.csv --candidates data\processed\taiwan_impact_candidates_20260115.csv --date 2026-01-15
.\.venv\Scripts\python.exe -m pytest
```

Run the Phase 2 news import check:

```powershell
python -c "from src.news_collectors.base import NewsItem; print('news import ok')"
```

Run the Phase 3 classifier import check:

```powershell
python -c "from src.signals.rule_based_classifier import classify_headline; print(classify_headline('Nvidia rises on strong AI chip demand'))"
```

Fixture mode is reproducible and uses synthetic sample metadata from `data/fixtures/sample_raw_news.json`. RSS mode is live and may depend on network and source availability:

```powershell
python scripts/collect_news.py --mode rss --feed-config data/fixtures/rss_feeds_example.json --date 2026-01-15
```

RSS mode stores feed-provided metadata and snippets only. It does not fetch full article bodies or scrape article pages.

Classification output is a research feature table saved under `data/processed/`. It is intended for later validation and must not be interpreted as a recommendation.

Taiwan impact candidate output is also saved under `data/processed/`. Unknown relationships become `unmapped` rather than invented.

Markdown report output is saved under `data/reports/`. The report is a deterministic research briefing and requires market validation.

## Research Guardrails

- Use public, reproducible data sources only.
- Do not scrape paywalled article bodies.
- Store publication timestamps and retrieval timestamps separately.
- Preserve ticker mapping assumptions rather than inventing relationships.
- Validate any signal claims through backtests before interpreting results.
- Use cautious research language such as potentially positive, potentially negative, watchlist, confidence level, possible impact, and requires validation.
