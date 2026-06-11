# AGENTS.md

## Project Overview

This repository is for a quantitative finance / AI research project:

"AI Pre-Market Briefing Agent: Mapping Overnight U.S. Financial News to Taiwan Equity Sector Signals"

The project goal is to build a reproducible Python pipeline that:
1. Collects overnight U.S. financial news and U.S. market data.
2. Classifies each news item by sector, ticker, sentiment, and Taiwan relevance.
3. Maps U.S. events to Taiwan-listed stocks or Taiwan sectors.
4. Creates structured daily pre-market reports before TWSE opens.
5. Backtests whether the generated news signals have explanatory or predictive power for Taiwan equity returns.

## Research Discipline

This is a quant research project, not a stock-picking app.

Do not make direct trading recommendations such as "buy", "sell", or "guaranteed to rise".
Use language such as:
- potentially positive
- potentially negative
- watchlist
- confidence level
- possible impact
- requires validation

## Core Research Question

Can overnight U.S. financial news signals provide incremental explanatory power for Taiwan sector or stock returns before the Taiwan market opens?

## Preferred Scope

Start with semiconductor / AI / hardware supply chain before expanding to all sectors.

Initial U.S. tickers:
- NVDA
- AMD
- AVGO
- MU
- INTC
- ASML
- TSM
- AAPL
- MSFT
- GOOGL
- AMZN

Initial Taiwan tickers:
- 2330.TW TSMC
- 2454.TW MediaTek
- 2303.TW UMC
- 3711.TW ASE
- 2317.TW Hon Hai
- 2382.TW Quanta
- 6669.TW Wiwynn
- 2408.TW Nanya Tech
- 2376.TW Gigabyte
- 2357.TW ASUS
- 2308.TW Delta Electronics

## Data Rules

Prefer APIs, RSS feeds, or reproducible public datasets.
Avoid scraping paywalled or copyright-restricted full articles.
Every news item must retain:
- source
- headline
- URL if available
- publication timestamp
- retrieval timestamp
- summary
- sector tag
- sentiment score
- affected U.S. tickers
- affected Taiwan tickers
- confidence score

## Anti-Hallucination Rules

Do not invent data.
Do not invent sources.
Do not invent ticker mappings without labeling them as assumptions.
When data is missing, write a clear TODO or fallback behavior.
All generated signals should be stored as structured data, not only prose.

## Engineering Rules

Use Python.
Use a modular structure.
Prefer pandas, numpy, requests, feedparser, yfinance, scikit-learn, statsmodels, and matplotlib.
Do not add heavy dependencies without asking first.
Do not hard-code API keys.
Use `.env` for secrets and provide `.env.example`.
Write code that works on Windows PowerShell.

## Suggested Repository Structure

data/
  raw/
  processed/
  reports/

src/
  config.py
  news_collectors/
  market_data/
  nlp/
  mapping/
  signals/
  backtest/
  reporting/

notebooks/
  01_exploration.ipynb
  02_backtest.ipynb

tests/

README.md
requirements.txt
.env.example

## Validation Standards

After editing code, run relevant checks.
If tests do not exist yet, create simple smoke tests.
For each module, include a small example or CLI command showing how to run it.
Before finishing, summarize:
1. Files changed.
2. What works.
3. What remains incomplete.
4. How to run or test the result.

## Research Evaluation Metrics

The project should eventually evaluate:
- direction accuracy
- average next-day return by signal bucket
- positive signal vs neutral signal vs negative signal
- open-to-close return
- close-to-close return
- hit ratio
- Sharpe ratio of simple signal strategy
- regression coefficient and t-statistic
- in-sample vs out-of-sample performance