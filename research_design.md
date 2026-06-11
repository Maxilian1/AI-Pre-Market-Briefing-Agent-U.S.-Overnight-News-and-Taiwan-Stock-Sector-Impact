# Research Design

## Research Question

Can overnight U.S. semiconductor / AI financial news signals provide incremental explanatory power for Taiwan semiconductor and AI supply-chain returns before TWSE opens?

## Hypotheses

H0:
Overnight U.S. semiconductor / AI news signals have no incremental explanatory power for Taiwan semiconductor / AI supply-chain stock returns.

H1:
Overnight U.S. semiconductor / AI news signals provide incremental explanatory power after controlling for U.S. market and sector returns.

## Live Mode vs Backtest Mode

Live mode simulates a pre-market workflow. It may only use information that would have been available before the configured Taiwan pre-market cutoff on the assigned Taiwan trading date.

Backtest mode evaluates archived news signals against later Taiwan returns. It must preserve original publication timestamps, retrieval timestamps, and signal-generation cutoffs so the research does not use future information.

## Overnight U.S. News Window

For Phase 1, the overnight U.S. news window is defined from the prior Taiwan market close through the configurable Taiwan pre-market cutoff on the next Taiwan trading date. News timestamps are normalized to UTC and converted to Asia/Taipei before assignment to a Taiwan trading date.

This initial definition handles weekdays and weekends. TWSE holiday handling is deferred to a later phase through a holiday calendar or holiday CSV.

## Taiwan Pre-Market Cutoff Assumption

The default Taiwan pre-market cutoff is 08:45 Asia/Taipei. News published after the cutoff is assigned to the next eligible weekday for research purposes.

The cutoff is configurable because production and backtest workflows may need to model data retrieval delays, vendor latency, or a stricter operational cutoff.

## Signal Construction Overview

The planned signal construction flow is:

1. Collect public news metadata without scraping paywalled article bodies.
2. Normalize publication and retrieval timestamps.
3. Deduplicate repeated or syndicated news items.
4. Tag relevant U.S. tickers and semiconductor / AI themes.
5. Map U.S. tickers or themes to Taiwan tickers and baskets using explicit mapping tables.
6. Assign each item to a Taiwan trading date using the pre-market cutoff.
7. Aggregate item-level signals into Taiwan ticker-level and basket-level research signals.
8. Store all generated signals as structured data before creating any prose report.

Phase 1 only creates the scaffold, static universe, seed mapping data, and timestamp utilities.

## Baseline Models

Baseline 1: Nasdaq / QQQ return only

Baseline 2: SOXX / SMH semiconductor ETF return only

Baseline 3: NVDA / AMD / TSM ADR return only

Baseline 4: News signal + market controls

## Evaluation Metrics

- Average return by signal bucket
- Hit ratio
- T-statistic
- Sharpe-like diagnostic
- Regression coefficient and t-statistic
- In-sample vs out-of-sample comparison

## Limitations

- Phase 1 does not collect live or historical news.
- Seed ticker mappings are research assumptions unless explicitly marked otherwise.
- Weekend handling is implemented first; TWSE holiday handling is a TODO.
- Timestamp quality can vary across data sources and must be audited before backtesting.
- News publication time and retrieval time can differ; live feasibility must use both.
- Duplicated syndicated news can overstate signal strength if not deduplicated.
- The initial universe is restricted to semiconductor / AI hardware supply-chain exposure and should not be generalized to all Taiwan equities.

## Non-Investment-Advice Disclaimer

This project is for quantitative research and educational analysis only. It does not provide investment advice, trading recommendations, or guarantees of future performance. Any signal produced by later phases must be interpreted as a research feature requiring validation, not as an instruction to buy or sell securities.
