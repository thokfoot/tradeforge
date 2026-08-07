# module: strategy-engine

**Purpose:** Create, validate, version, and manage strategies — no-code (visual) and code (Python) modes. Strategies are versioned in git (per user) for traceability.

**Contract:** `Strategy` / `StrategyService` (see `../shared/contracts/README.md`).

**Key features (Phase 1+):**
- No-code builder config → structured strategy JSON
- Validation (indicator ranges, symbol validity, risk sanity)
- Git-backed versioning: every change = new version (user's own traceable history)
- AI assistant can create strategies via this module's contract

**Isolation:** Owns strategy storage exclusively. Never touches trade/backtest data.

**Status:** Planning.
