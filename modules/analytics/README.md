# module: analytics

**Purpose:** Performance analytics + trading journal. Turns raw trades into insight.

**Contract:** `Analytics` (see `../shared/contracts/README.md`).

**Features:**
- Metrics: win rate, profit factor, max drawdown, expectancy, R-multiple, average hold time, streaks, monthly P&L
- Equity curve (chart)
- Trading journal: tag trades, add notes, screenshots, lessons
- Reports/export (CSV, and later PDF)

**Isolation:** Pure analysis — reads trades via contract, never mutates them.

**Status:** Planning. Journal is a Phase 2 item; metrics module powers Phase 1 results pages.
