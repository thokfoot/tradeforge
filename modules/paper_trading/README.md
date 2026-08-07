# module: paper-trading

**Purpose:** Real-time paper (simulated) trading on live prices. Virtual balance, full order types, resettable account.

**Contract:** `PaperTrader` (see `../shared/contracts/README.md`).

**Features:**
- Virtual account (default e.g. ₹1,00,000 / $100,000), resettable
- Order types: market, limit, SL, bracket (SL+TP)
- Positions / working orders / history tracking
- Realistic fills using live/delayed feed
- **Parity scoring:** compares paper results vs backtest expectations → shows users when a strategy underperforms live (our realism promise)

**Safety:** Paper only — module cannot place real orders by design (no broker integration).

**Isolation:** Owns user paper accounts exclusively. Reads market data via contract.

**Notes (2026-08-07):** `replay_trades(store, user_id, fills)` replays historical fills (symbol, side, qty, price) as MARKET orders through the normal order path — balance/position rules still apply. `reset_account(user_id, capital)` accepts a custom starting capital (used by `/api/paper/replay`).

**Status:** Implemented.
