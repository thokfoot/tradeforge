# module: backtest-engine

**Purpose:** Event-driven (bar-by-bar) backtesting with realistic costs. THE trust moat.

**Contract:** `BacktestEngine` (see `../shared/contracts/README.md`).

**Core requirements (locked):**
- Event-driven, no look-ahead (decisions only on data available at bar close)
- **Indian cost model:** brokerage + STT + GST + SEBI charges + stamp duty (per segment)
- US fees + crypto maker/taker fees
- Slippage model; realistic fills
- Order types: market, limit, stop-loss, bracket
- Metrics: win rate, profit factor, max drawdown, expectancy, R-multiple, equity curve, per-trade log
- **Reproducible hash:** (strategy code version + data version + params) → any result regenerable

**Isolation:** Pure computation — reads data + strategy via contracts, returns results. No side effects. Queued via Redis workers so heavy runs never block the API.

**Notes (2026-08-07):** Interval-agnostic (1m/1h/1d all work — fill at open[t+1] of the next bar). `pct` sizing floors to whole shares but buys at least 1 share if the allocation can't afford one (otherwise high-price symbols like BTC never trade).

**Status:** Implemented.
