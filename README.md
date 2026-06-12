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

## Phase 5.5 Status

Phase 5.5 adds documented live RSS mode configuration:

- Provides `data/fixtures/rss_feeds_real.example.json` as a real RSS configuration template.
- Keeps local `data/fixtures/rss_feeds_real.json` out of source control.
- Documents how to run the existing pipeline on live RSS metadata.

Phase 5.5 does not add API collectors, scrape article bodies, ingest market data, run backtests, or change classifier, mapping, or report logic.

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

## Live RSS Mode

Fixture mode is reproducible and is used for automated tests. Live RSS mode depends on network access, source availability, and each feed's current metadata. Live RSS output is a research artifact, not investment advice.

Create a local feed config from the example:

```powershell
Copy-Item data\fixtures\rss_feeds_real.example.json data\fixtures\rss_feeds_real.json
```

Run the live metadata pipeline:

```powershell
.\.venv\Scripts\python.exe scripts\collect_news.py --mode rss --feed-config data\fixtures\rss_feeds_real.json --date YYYY-MM-DD
.\.venv\Scripts\python.exe scripts\classify_news.py --input data\raw\news_YYYYMMDD.csv --date YYYY-MM-DD
.\.venv\Scripts\python.exe scripts\map_taiwan_impacts.py --input data\processed\news_signals_YYYYMMDD.csv --date YYYY-MM-DD
.\.venv\Scripts\python.exe scripts\generate_report.py --signals data\processed\news_signals_YYYYMMDD.csv --candidates data\processed\taiwan_impact_candidates_YYYYMMDD.csv --date YYYY-MM-DD
```

Replace `YYYY-MM-DD` with a real ISO date such as `2026-06-11`; placeholder values are rejected by the CLI. RSS mode stores only feed metadata and RSS-provided snippets. Article pages are not scraped, paywalled websites are not scraped, and full article bodies are not collected. Google News RSS entries in the example config are experimental aggregator sources; source provenance should be interpreted as aggregator metadata. Historical backtesting requires archived news or a proper historical news API/dataset.

## Live RSS QA and Rule Calibration

Google News RSS may include aggregator HTML and URLs such as `news.google.com/rss/articles/...` inside summaries. The classifier ignores source/provider names, feed names, href URLs, and RSS provider labels so these artifacts do not become ticker or sector signals.

Run QA before using live RSS artifacts for research:

```powershell
.\.venv\Scripts\python.exe scripts\qa_signal_distribution.py --signals data\processed\news_signals_YYYYMMDD.csv
```

The QA script reports source-sector counts, sector-theme counts, suspicious Cloud/Data Center rows, GOOGL matched-rule counts, and top matched rules. It exits non-zero if known Google News overmatching patterns appear. Live RSS output should be treated as unvalidated research data until this QA check passes.

## Phase 5.7 Report QA

Phase 5.7 improves deterministic report presentation quality. It adds report-level Taiwan candidate aggregation, a separate Market Context Signals section for Macro and Energy items, external-headline labeling, and a post-run report QA script. It does not validate market performance.

Run report QA after generating a report:

```powershell
.\.venv\Scripts\python.exe scripts\qa_report_output.py --report data\reports\taiwan_premarket_report_20260611.md --signals data\processed\news_signals_20260611.csv --candidates data\processed\taiwan_impact_candidates_20260611.csv
```

The report QA script checks required sections, repeated watchlist rows, awkward redaction artifacts, source provenance, Market Context Signals, and research disclaimers. Phase 6 will handle market data ingestion and backtest validation.

## Phase 6A Return Labels

Phase 6A adds market data ingestion and return label construction. It builds outcome labels for later validation only; it does not prove signal effectiveness, run regressions, perform event studies, or backtest a strategy.

Fixture mode is reproducible and does not use the network:

```powershell
.\.venv\Scripts\python.exe scripts\download_market_data.py --mode fixture --start 2026-01-12 --end 2026-01-20 --output data\processed\prices_fixture.csv

.\.venv\Scripts\python.exe scripts\build_return_labels.py --candidates data\processed\taiwan_impact_candidates_20260115.csv --prices data\processed\prices_fixture.csv --date 2026-01-15
```

Live yfinance mode is for manual research runs and may depend on vendor availability or later data revisions:

```powershell
.\.venv\Scripts\python.exe scripts\download_market_data.py --mode yfinance --start 2026-06-01 --end 2026-06-13 --output data\processed\prices_20260611.csv

.\.venv\Scripts\python.exe scripts\build_return_labels.py --candidates data\processed\taiwan_impact_candidates_20260611.csv --prices data\processed\prices_20260611.csv --date 2026-06-11
```

Phase 6A output is saved as `data/processed/return_labels_YYYYMMDD.csv`. Return fields such as `prev_close_to_open_return`, `open_to_close_return`, `close_to_close_return`, and `next_close_to_close_return` are outcome labels for Phase 6B validation. They must not be used in signal generation. Taiwan holidays and weekends are handled through the trading dates present in the price data rather than calendar-day assumptions.

## Phase 6B Event-Study Diagnostics

Phase 6B adds deterministic event-study diagnostics on Phase 6A return labels. It aggregates repeated same-day same-target news-candidate rows before calculating return bucket summaries, directional hit ratios, and simple descriptive t-statistics.

Fixture or local return-label run:

```powershell
.\.venv\Scripts\python.exe scripts\run_event_study.py --return-labels data\processed\return_labels_20260115.csv --date 2026-01-15
```

Live return-label run:

```powershell
.\.venv\Scripts\python.exe scripts\run_event_study.py --return-labels data\processed\return_labels_20260611.csv --date 2026-06-11
```

Outputs are saved as:

- `data/processed/event_study_results_YYYYMMDD.csv`
- `data/processed/event_study_aggregated_YYYYMMDD.csv`
- `data/reports/event_study_summary_YYYYMMDD.md`

Phase 6B does not prove predictive power. One-day or fixture results are pipeline validation only. Meaningful evidence requires many archived days, baseline controls, and longer out-of-sample testing in Phase 6C or later.

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
