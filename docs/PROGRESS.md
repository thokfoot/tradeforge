# Session Progress Log

Append at the end of every working session. This is the history of what was actually done.

Format:
```
## YYYY-MM-DD — <short title>
- What was done (bullets)
- What is blocked / next
```

---

## 2026-08-07 — Phase 1 M7–M10 (paper trading, strategies, AI assistant, frontend) — "complete it"
- **M7 paper trading** (`modules/paper_trading/`): `AccountStore` + `Ledger` (JSON persistence per user), `PaperTraderService` (MARKET/LIMIT fills, rejections for insufficient funds/position, positions/history/reset/account — equity = balance + cost_basis + unrealized; `parity_score` = win rate). 12 tests. Live API verified: AAPL BUY 5 filled @ 312.62, equity stayed 100000.
- **M8 strategy storage + sandbox** (`modules/strategy_engine/`): `sandbox.py` `run_code` (restricted `__builtins__` whitelist, thread timeout 2s), `store.py` (JSON version history), `service.py` `StrategyService` (validate on probe data / save / list_versions). 10 tests. Contract satisfied via Protocol check.
- **M10 AI assistant MVP** (`modules/ai_assistant/`): `GeminiProvider` (google-generativeai, lazy import), `AIAssistantService` (chat with teacher persona, extracts ```python blocks → validates via sandbox, propose/confirm_action flow). 6 tests.
- **API wiring** (`app/api/{paper,strategies,assistant}.py`, expanded `deps.py`): `/api/paper` (order/account/positions/history/reset), `/api/strategies` (save/validate/versions), `/api/assistant` (chat/confirm, 409 on no pending action). CORS added for dev origin. `requirements.txt` += `google-generativeai`.
- **M9 frontend** (`frontend/`): Next.js 16 (TS, App Router) + TradingView lightweight-charts v5 + PWA (manifest + sw.js + icons). One page: market/symbol picker → candlestick chart → backtest runner (code, metrics grid, trades table). Live verified on :3000 against API :8000 (CORS preflight OK).
- **Test suite: 86 passing** (`python -m pytest modules app`). Fixed pytest basename collision (`test_service.py` in two module dirs → renamed to `test_paper_service.py` / `test_strategy_service.py`).
- Commits: `0955737` (M7/M8/M10 + API), `9250aee` (M9 frontend).

**Next:** Phase 1 wrap — auth/billing, VPS deploy via docker compose, data backfill, run guide. Then Phase 2 (intraday/replay, screener, journal). See NEXT-STEPS.md.

## 2026-08-07 — Phase 1 M6 (data + backtest API)
- `app/providers.py` — `get_provider(market)` factory (IN/US/CRYPTO → adapter behind `MarketDataProvider` contract), ParquetStore rooted at `DATA_DIR`.
- `app/api/deps.py` — `provider_for(market)` (module-attr so tests monkeypatch cleanly).
- `app/api/market.py` — `GET /api/symbols?market=` + `GET /api/ohlcv/{symbol}?market=&interval=&start=&end=` (bars: date/open/high/low/close/volume; 404 on no data; 422 on bad interval).
- `app/api/backtest.py` — `POST /api/backtest` (market, symbol, interval, range, strategy code/params, config, costs) → serialized BacktestResult (equity curve, trades, metrics with inf→null, run_hash).
- Live verified: /health, /api/symbols (US=45), /api/backtest (BTCUSDT, 38 bars).
- **Test suite: 51 passing.** (Found + fixed: `from deps import provider_for` didn't respond to monkeypatch → real NSE network in tests; switched to `deps.provider_for`. Also `.gitignore` now ignores all of `data/`.)

**Next:** M7 paper trading → M8 strategy storage/sandbox → M9 frontend+charts → M10 AI MVP. See NEXT-STEPS.md.

## 2026-08-07 — Phase 1 build M1–M5 (backend foundation)
- **M1** FastAPI scaffold: `app/` + config (pydantic-settings) + `/health` + Dockerfile + compose + `.env.example` (verify: `uvicorn app.main:app` → /health OK).
- **M2** Contracts package (owner-approved): `modules/shared/contracts/` — 8 runtime-checkable Protocols + 18 data models (`models.py`, `interfaces.py`). Note: `place_order(user, ...)` → `user_id`; `BacktestEngine.metrics` → `Metrics`.
- **Module renames:** hyphenated module folders → underscore (`modules/market_data`, `modules/backtest_engine`, ...) so they're importable as packages.
- **M3** India adapter: `NSEArchiveProvider` — canonical OHLCV + delivery fields, symbol master (stocks + 163 indices slugged), `ParquetStore`, `scripts/backfill_india.py`. Live verified: RELIANCE quote 1334.8 (2026-08-07), 3445 symbols.
- **M4** `ParquetBackedProvider` base (store-backed, gap-filling fetch, on-demand). `YFinanceProvider` (US; AAPL 252 rows/1y, quote 314.08, 45 curated symbols) + `BinanceProvider` (crypto; BTCUSDT 31 rows/30d, quote 64958, 489 USDT pairs).
- **M5** Backtest engine: `EventDrivenEngine` (bar-by-bar, signal[t] → fill at open[t+1], no look-ahead), Indian cost model (`order_charges`: brokerage/STT/exchange/SEBI/GST/stamp/slippage), metrics (CAGR/Sharpe/Sortino/MDD/win-rate/PF/Calmar), reproducible sha256 hash. Golden scenario hand-verified. Live: `scripts/smoke_backtest.py` ran SMA-20 on real RELIANCE.
- **Test suite: 45 passing** (`python -m pytest modules`).
- **Known limitation:** NSE bhavcopy is per-day → backfill ~1 req/day (slow for long ranges); US 1m = only ~1 week free; provider store is day-granular (intraday partial-day gaps not refetched).

**Next:** M6 API endpoints → M7 paper trading → M8 strategy storage/sandbox → M9 frontend+charts → M10 AI MVP. See NEXT-STEPS.md.

## 2026-08-07 — Data PoC (Phase 0.5) — all 3 markets verified
- Created `data-poc/` scripts: `poc_india.py`, `poc_us.py`, `poc_us2.py`, `poc_us3.py`, `poc_us4.py`, `poc_crypto.py`.
- **India (nse-archives) ✅** — bhavcopy 2026-08-06: 3287 stocks (OHLC+volume+delivery), 163 indices (Nifty 50 etc., with P/E). Historical dates work. No split adjustment info → adjustment policy needed later.
- **US: Stooq ❌ (404 on all symbols)** → **yfinance ✅** — AAPL 10y daily = 2514 rows; 1h = 1yr; 1m = only last ~5–7 days (paid source needed for 1m later).
- **Crypto (Binance) ✅** — daily + 1m klines (1000/call, paginate), no auth; `data.binance.vision` monthly archives free & deep (BTCUSDT 1m Jan-2020 tested).
- **Locked Phase-1 providers:** India=nse-archives bhavcopy, US=yfinance, Crypto=Binance. Updated DATA-LAYER.md + RESEARCH.md.

**Next:** Phase 1 build — M1 repo scaffold, M2 contracts, M3 India adapter. See NEXT-STEPS.md.

## 2026-08-07 — Project kickoff (planning + skeleton)
- Researched market (2026): Streak, Tradetron, TradingView, Tickertape, Sensibull, Backtrex, TradeZella, Chartink; new-trader needs by level; free data sources for India/US/Crypto; open-source backtest engines (backtesting.py, vectorbt, backtrader, NautilusTrader).
- Held product decisions with owner (Hinglish): git reimagined, cloud server not home PC, freemium not cheapest-race, all markets daily in Phase 1, intraday phased, PWA first, Gemini free tier AI, realistic backtesting.
- Created repo skeleton at `C:\trade-forge`: docs/ (plan, roadmap, decisions, progress, next-steps, research, architecture, product, legal), modules/ (10 backend modules + shared/contracts), frontend/.
- Wrote AGENTS.md (auto-load context file) + all planning docs.
- Git initialized + initial commit (see git log).

**Next:** Phase 0.5 — data-source proof-of-concept (India/US/Crypto fetch test). See NEXT-STEPS.md.
