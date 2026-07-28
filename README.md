# paper-trading-diary

Comparing systematic and discretionary paper trading decisions over time, with a logged diary of reasoning and outcomes for each.

## What this is

Two paper trading tracks run in parallel:

- **Systematic (Alpaca API)** — trades executed by a script based on a defined signal. Currently starting with a simple baseline (moving average crossover), with plans to incorporate signals derived from prediction intervals in [Conformal Alpha Research](https://github.com/temi-salau/conformal-alpha-research) as the signal matures.
- **Discretionary (Investopedia simulator)** — trades placed manually, based on my own read of the market at the time.

Every decision on both tracks is logged in the same format, so the two approaches can be directly compared over time: what triggered the trade, what the reasoning was, and how it played out.

## Why

Backtesting alone doesn't capture what it's like to make a call in real time. This tracks both a systematic and a discretionary approach side by side, to build a real record of decision-making under uncertainty, and to see where the two agree, disagree, and diverge in performance.

## Structure

```
/systematic/       - signal logic and Alpaca execution scripts
/discretionary/     - raw manual trade logs (ticker, size, entry/exit price, return)
/diary/             - dated entries for both tracks: decision, reasoning, outcome, reflection
```

## Diary format

Each entry follows:

- **Date**
- **Platform** (Alpaca / Investopedia)
- **Decision** (buy/sell/hold, ticker, size)
- **Reasoning**
- **Outcome** (filled in after the fact)
- **Reflection**

## Status

Started July 2026. Ongoing.

## Stack

Python, Alpaca API, pandas
