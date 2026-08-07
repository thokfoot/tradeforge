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

**Status:** Planning. Implement after data layer + contracts.
