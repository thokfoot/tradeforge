# NEXT STEPS — start here next session

> If you are an AI agent or the owner opening this project again: read AGENTS.md first, then this file.

## Current state (short)

Phase 0 (Planning) ✅ and **Phase 0.5 (Data PoC) ✅ — all three markets verified** and committed.
Free sources that WORK:
- **India:** `nse-archives` bhavcopy (per-day file, all stocks + 163 indices) — verified
- **US:** yfinance (Stooq is 404/dead) — verified: daily ~10y, 1h 1yr, 1m only last week
- **Crypto:** Binance public API + `data.binance.vision` archives — verified (even 1m is free)

**Next real task: Phase 1 build — first milestone = repo scaffold + contracts + India data adapter.**

## Next task: Phase 1 build (run in this order)

### M1 — Repo scaffold (backend foundation)
- [ ] Create `requirements.txt` (fastapi, uvicorn, sqlalchemy, pandas, numpy, pyarrow, redis, httpx)
- [ ] Create `app/` package skeleton + `main.py` (FastAPI app with /health endpoint)
- [ ] Config via `.env` + pydantic settings
- [ ] Dockerfile + docker-compose (app + postgres + redis)
- [ ] `make`-style run scripts / README note

### M2 — Contracts (foundation; get owner approval on names)
- [ ] Implement `modules/shared/contracts/` as Python package with Protocol classes (from the README):
  `MarketDataProvider`, `Strategy/StrategyService`, `BacktestEngine`, `PaperTrader`, `Analytics`, `AIAssistant`, `AuthService`, `NotificationService`
- [ ] Add per-module placeholder test that imports the contract (proves no cross-module leakage)

### M3 — India data adapter (first real module code)
- [ ] Implement `MarketDataProvider` for `nse-archives` (daily EOD)
- [ ] Normalize to canonical OHLCV schema (see DATA-LAYER.md)
- [ ] Symbol master fetch (NSE symbols + indices)
- [ ] Backfill job: fetch N trading days, write Parquet (partitioned by symbol/year)
- [ ] Cache + on-demand fetch for non-preloaded symbols
- [ ] Module tests (small fake provider + real 1-day fetch)

### M4 — US + Crypto adapters (same interface, ~1–2 days each)
- [ ] US: yfinance adapter (daily)
- [ ] Crypto: Binance adapter (daily + kline pagination)
- [ ] Tests per adapter

### M5 — Backtest engine core
- [ ] Event-driven loop (bar-by-bar, no look-ahead)
- [ ] Indian cost model + slippage
- [ ] Metrics + reproducible hash
- [ ] Tests (golden strategy result)

> Full Phase 1 scope (charts, paper trading, screener, AI MVP, auth, frontend) — see docs/PLAN.md and docs/ROADMAP.md.

## Rules to remember every session

- **Update AGENTS.md + PROGRESS.md + NEXT-STEPS.md at end of session.**
- **Module isolation is the owner's #1 rule:** changes live inside one module; run that module's tests; never let one feature break another.
- Explain things to the owner in simple Hinglish; keep repo docs in English.
- No code comments unless asked. Commit after meaningful milestones only.
