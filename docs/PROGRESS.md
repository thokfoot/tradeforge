# Session Progress Log

Append at the end of every working session. This is the history of what was actually done.

Format:
```
## YYYY-MM-DD — <short title>
- What was done (bullets)
- What is blocked / next
```

---

## 2026-08-08 — Local release candidate sign-off
- **Local production stack verified:** backend runs without `--reload` on `:8000`; frontend uses the standalone server on `:3000` with `npm start` corrected to `node .next/standalone/server.js`; both health checks return 200 and the frontend has no Next dev indicator.
- **Market data:** local-first development mode now avoids remote gap hangs when Parquet data exists; weekend/holiday 404s are cached as missing trading days. India backfill script fixed (keyword dates), supports `--days`/`--all-stocks`, and batch-saves progress.
- **India local dataset:** 3,462 NSE stock/index Parquet files after a 30-day all-stock backfill; representative Nifty 50/Bank Nifty constituents and major indices have a 90-day window. NIFTY 50, NIFTY BANK, and NIFTY TOTAL MARKET smoke-tested. US: 46 files. Crypto: 2 files.
- **Smoke verified:** IN/US/CRYPTO symbols and OHLCV, RELIANCE and NIFTY index backtests, India screener, India paper BUY/SELL + reset, demo Pro login, frontend production response.
- **Tests:** 180 passing after the provider, AI-context, and backfill changes.
- **UI polish:** desktop/mobile shell, readable line-icon navigation, hover/focus animations, command palette, beginner Learn/Builder entry points, responsive chart, bottom-right floating AI assistant, market/index filters, strategy templates, sticky controls, and distinct execution CTA.
- **AI quality:** assistant prompt now knows the actual product capabilities and avoids recommending existing modules as new ideas; delayed responses show `Thinking...`.
- **Next:** local acceptance is complete; remaining work is optional deeper India history and later VPS/domain/HTTPS deployment.

## 2026-08-08 — Phase 3 wrap: Watchlists + Hindi i18n + Onboarding + Admin
- **Watchlists** (`modules/watchlists/`): `WatchlistStore` (per-user JSON, add/remove/list per market). `POST/GET/DELETE /api/watchlists/*` (login-gated). Frontend Watchlist tab — add symbol per market, chips clickable → navigate to dashboard. 5 tests.
- **Full Hindi UI** (`frontend/lib/i18n.tsx`): `I18nProvider` + `useT()` / `useLang()` hooks. Translation map covering all tabs, buttons, labels, errors, disclaimer. EN/HI toggle in header applies to entire app.
- **Onboarding wizard** (`components/Onboarding.tsx`): 5-step guided flow for new visitors — welcome, charts, backtest, paper trading, final tips. Stores `tf_onboarding_done` in localStorage. EN/HI toggle built-in.
- **Admin dashboard** (`components/Admin.tsx`): Simple server status via `/health` + capability summary. Shown only for admin email.
- **180 tests green** (watchlist +5 plus AI product-context coverage), frontend build verified.

**Phase 1–3: all planned items complete.** Only VPS test (needs server with Docker) remains.

## 2026-08-08 — Phase 3: Postgres migration (SQLAlchemy models + PG stores)
- **SQLAlchemy models** (`modules/shared/models.py`): 15 tables — `users`, `sessions`, `strategies`, `journal_entries`, `alert_rules`, `alert_notifications`, `saved_scans`, `education_progress`, `paper_accounts`, `paper_positions`, `paper_orders`, `paper_trades`. All with proper FKs, indexes, JSONB for tags/filters/params.
- **PG-backed store variants** (`modules/shared/pg_stores.py`): `PgUserStore`, `PgJournalStore`, `PgAlertStore`, `PgScanStore`, `PgEducationStore`, `PgStrategyStore`, `PgAccountStore` — all matching existing JSON store interfaces exactly.
- **Infrastructure** (`modules/shared/database.py`): Engine/session factory, `init_db()` auto-creates tables, `use_postgres()` config gate.
- **Config**: `DB_BACKEND` env var (`json` default, `postgres` for PG). `app/config.py`, `.env.example` updated.
- **Dependency injection** (`app/api/deps.py`): Every store factory checks `use_postgres()` and creates PG or JSON variant accordingly.
- **App startup** (`app/main.py`): `init_db()` called in lifespan when `DB_BACKEND=postgres`.
- **Migration script**: `scripts/migrate_to_pg.py` — one-shot copy all JSON data → Postgres tables. Run after switching to `DB_BACKEND=postgres`.
- **174 tests green**. Backward compatible: default is `json`, zero disruption to existing installs.

**Next:** VPS test. See NEXT-STEPS.md.

## 2026-08-08 — Phase 3 #1–#5: Tauri .exe, Education tab, Demo account
- **Tauri .exe built successfully!** Installed Rust 1.97.1 (GNU toolchain via `winget install Rustlang.Rustup` + MSYS2 MinGW `C:\msys64` for `dlltool.exe`). `npm run tauri build` → `frontend/src-tauri/target/release/trade-forge.exe` (21.8 MB). Icon generated from existing PWA icon via Pillow → `icon.ico`.
- **Education tab** — new Learn tab in frontend: 12 lessons across 6 sections (Getting Started, Backtesting, Technical Indicators, Paper Trading, Strategy Builder, Risk Management). Each lesson has English + Hinglish versions, collapsible accordion. EN/HI language toggle. Content in `frontend/lib/lessons.ts`, component `Education.tsx`. Covers: what is trading, why backtest, reading results, RSI/SMA/MACD/Bollinger, paper trading how-to, replay feature, builder blocks, position sizing, drawdown, Indian brokerage costs.
- **Demo account seeded** — `scripts/seed_demo.py`: `demo@tradeforge.in` / `tradeforge123` Pro account with 6 sample journal entries (AAPL buy/sell, TSLA reversal, RELIANCE value, BTCUSDT allocation) with realistic tags/ratings/lessons.
- **Data store check** — 1.8 MB, 56 files. US coverage decent (43 parquet symbols). Smoke test passes. NSE India data not yet backfilled (needs ~1 req/day — slow).
- **174 tests green**, frontend builds (standalone + export) verified.

**Next:** Postgres migration (JSON→SQLAlchemy), VPS test. See NEXT-STEPS.md.

## 2026-08-08 — Phase 2 #6–#7: Tauri desktop wrapper + VPS deployment
- **Tauri desktop wrapper** (`frontend/src-tauri/`): Full Tauri v2 config + Rust backend (`Cargo.toml`, `main.rs`, `lib.rs`, `build.rs`, `capabilities/default.json`). Config: `tauri.conf.json` (dev → localhost:3000, prod → `output:export`).
- **Native Windows notifications**: `lib/tauri-notify.ts` (detects Tauri runtime, requests notification permission, `notifyAlert()` bridges alert notifications to OS). Wired into Alerts component — new notifications fire native OS toasts. `TauriNotifyInit` component asks for permission on load.
- **Build**: `next.config.ts` conditional export mode (`NEXT_EXPORT=1`), `build:export` + `tauri` scripts in package.json, `cross-env` for cross-platform env vars. `types/tauri.d.ts` silences TS module errors.
- **VPS deploy**: `scripts/deploy.sh` (--setup installs docker + clones + prompts for .env + `docker compose up`, --ssl DOMAIN runs certbot + swaps nginx SSL config, default = git pull + up). `nginx/nginx-ssl.conf` (HTTPS + Let's Encrypt paths).
- **Compose updates**: port 443, certbot volume, `NGINX_CONF` env var (swap configs), `ENVIRONMENT` pass-through, `NEXT_PUBLIC_API_URL` build arg for frontend.
- **Both builds verified** (standalone + export), 174 tests green.
- **Cannot build Tauri .exe yet**: Rust not installed on this machine. All code/config ready — install Rust → `cargo tauri dev/build`.
- **Cannot test VPS deploy**: Docker not installed on this machine. Script + config ready — copy repo to VPS → `bash scripts/deploy.sh --setup`.

**Next:** Phase 3 — install Rust + build Tauri .exe, in-app Education, Postgres migration, seed demo account, data backfill, VPS test. See NEXT-STEPS.md.

## 2026-08-07 — Phase 2 #5: No-code strategy builder (visual blocks → runnable code)
- **New module `modules/strategy_builder/`** (pure code generator, no cross-module imports): `StrategyBuilder.generate(spec)` produces engine-ready Python; `validate(spec)` checks structure (allowed indicators/ops/join, numeric values, at least one condition).
- **Blocks**: indicators `close/open/high/low/volume/sma/ema/rsi` × `above`/`below` × numeric threshold OR vs another indicator (e.g. `close above sma20`); entry & exit rules each join with AND/OR; empty exit defaults to `exit = ~entry`.
- **State machine**: flat → buy when entry true (fill next open), holding → sell when exit true (fill next open) — matches engine 0/1 semantics. Generated code uses only top-level names: the restricted sandbox forbids `import` and splits globals/locals (which breaks helper-function patterns), so RSI is precomputed as `rsi_{period}` and the loop is top-level. Runs in BOTH the engine namespace and `StrategyService.validate()` sandbox.
- **API** (`app/api/builder.py`): `POST /api/builder/generate` (Pro-gated `require_plan`) → `{name, code, valid, errors, warnings}` after a real sandbox validation pass via `deps.strategy_service().validate(probe)`.
- **Frontend**: new "Strategy Builder" tab — entry/exit block rows (indicator / period / op / threshold-or-ref), AND/OR join selectors, add/remove rows, Generate, code preview, and an inline backtest runner (market/symbol/interval + metrics).
- **Test suite: 174 passing** (was 161; +9 builder module, +4 builder API). Live verified: RSI-pullback spec (RSI<40 buy, RSI>60 sell) → `valid=True` → real AAPL 1d 2024→2026 backtest ran (10 trades, +4.46%).
- Also: blanked the real `GEMINI_API_KEY` that was committed in `.env.example` (commit `cff5bf2`) — owner should rotate it.
- Commit: `f42f439` (no-code builder + docs).

**Next:** Phase 2 — Tauri desktop wrapper, real VPS deploy. See NEXT-STEPS.md.

## 2026-08-07 — Phase 2 #4: Alerts (price + RSI, in-app notifications)
- **New module `modules/alerts/`** (isolated, no cross-module imports): `AlertRule` + `AlertNotification` added to shared contracts (models + `AlertService` Protocol, additive); `AlertStore` (per-user JSON: rules + notifications, capped 200); `AlertService` (create/list/delete/notifications/clear + `check_user`/`check_all`). RSI(14) is a local copy of the Wilder formula — never touches screener internals.
- **Rule model**: PRICE or RSI metric × ABOVE/BELOW condition × target value. One-shot: on hit the rule flips `active=False` and appends an in-app notification (no spam). Provider errors on one rule are skipped, never crash the check.
- **API** (`app/api/alerts.py`): `POST /api/alerts` (create, login-gated, 422 on bad metric/condition/non-positive value), `GET /api/alerts`, `DELETE /api/alerts/{rule_id}`, `GET /api/alerts/notifications`, `POST /api/alerts/notifications/clear`, `POST /api/alerts/check`. `deps.alert_service()` singleton.
- **Background worker**: `app/main.py` lifespan starts an asyncio loop calling `check_all(provider_for)` every `alert_check_interval_seconds` — only when `settings.alerts_enabled` (`ALERTS_ENABLED=0` default; enable on VPS). TestClient runs don't start it.
- **Frontend**: new Alerts tab — form (symbol/market/metric/condition/value), Add + Check-now buttons, rules list with delete + active/fired status, notifications list + clear.
- **Test suite: 161 passing** (was 146; +11 alerts module, +4 alerts API). Live verified: create PRICE-ABOVE-50 AAPL rule → `POST /api/alerts/check` fired on real quote 312.96 (Hinglish message, rule deactivated) → notification listed → delete → clear. BTCUSDT RSI-ABOVE-80 stayed active (not triggered — realistic).
- Commit: `b77c811` (alerts + docs).

**Next:** Phase 2 — no-code strategy builder, Tauri, real VPS deploy. See NEXT-STEPS.md.

## 2026-08-07 — Phase 2 #3: Journal AI review (Gemini reads your trading journal)
- **Contract**: `AIAssistant` Protocol (in `modules/shared/contracts/interfaces.py`) gains `review_journal(user_id, entries) -> str`. Additive — no other consumer changed.
- **Service**: `modules/ai_assistant/service.py` `review_journal()` — builds a text summary of the last 30 entries (symbol/side/pnl/rating/tags/note/lesson) → Hinglish prompt asking for observed patterns, strengths, risks, and 3 improvement points (educational framing, no advice). `try/except` → friendly fallback message on provider error. Same for `chat()`.
- **API**: `POST /api/journal/review` (`app/api/journal.py`) — loads entries via `deps.journal_service()`, calls `deps.assistant_service().review_journal(...)`, returns `{text, entries}`. Pro-gated with `deps.require_plan("pro")`.
- **Frontend**: `frontend/lib/api.ts` `journalReview(userId, token)`; Journal tab gets "🤖 AI Review my Journal (Pro)" button (disabled without token/entries, shows spinner + ai-reply box). `page.tsx` now passes token/user to Journal.
- **Test suite: 146 passing** (was 141). Live verified: register→subscribe(pro)→2 journal entries→`POST /api/journal/review` returned real Gemini Hinglish feedback referencing the actual AAPL (momentum/patience) and TSLA (revenge) entries. Unauthorized → 401.
- Commit: `9837f12` (journal AI review + docs).

**Next:** Phase 2 — alerts (Redis-backed), no-code builder, Tauri, real VPS deploy. See NEXT-STEPS.md.

## 2026-08-07 — Phase 2 #2: Screener 2.0 (indicators + saved scans)
- **New indicators** on `ScreenerRow` (additive, backward compatible): `rsi_14` (Wilder ewm), `bb_position` (Bollinger %B 20,2), `vol_ratio_20` (last vol / prior-20 avg), `above_sma_20`, `macd_above_signal`. New filters: `min/max_rsi`, `min/max_bb_position`, `min_vol_ratio`, `above/below_sma_20`, `macd_above/below_signal`. New sortable: `rsi_14`, `bb_position`, `vol_ratio_20`.
- **Saved scans** (`modules/screener/scans.py`): `SavedScan` + `ScanStore` (per-user JSON). API: `POST /api/screener/scans/save`, `GET /api/screener/scans`, `DELETE /api/screener/scans/{id}`, `POST /api/screener/scans/{id}/run` — all gated by login token (`current_user`).
- **Frontend**: Screener tab now has RSI/%B/vol-ratio/SMA20/MACD filters, sort dropdown, and Saved Scans (name → save, run, delete chips). `page.tsx` passes token/user to Screener.
- **Test suite: 141 passing** (was 131). Live verified: US scan RSI>60 (matches), save→list→run-by-id (MSFT top)→unauth 401→delete. Note: first live scan attempt hung on cold yfinance — retry was fast; consider a per-symbol fetch timeout later.
- Commit: next = screener 2.0.

**Next:** Phase 2 — journal AI review, alerts, no-code builder, Tauri, real VPS deploy. See NEXT-STEPS.md.

## 2026-08-07 — AI live + Phase 2 start: Intraday & paper replay
- **AI assistant now LIVE with real Gemini key.** Owner pasted `GEMINI_API_KEY` in `.env`; wired via `settings.gemini_api_key` (pydantic `extra="ignore"` so `NEXT_PUBLIC_API_URL` in `.env` no longer breaks `Settings()`). Model default → `gemini-flash-latest` (2.0-flash no longer exists), overridable via `GEMINI_MODEL`. `chat()` returns a friendly message instead of 500 when the provider errors. Live verified: real Gemini Hinglish reply for "RSI kya hota hai?". Note: first key had "429 prepayment credits depleted" → owner created a new Google project + key; that one works.
- **Phase 2 #1 — Intraday + replay (US/Crypto 1m/1h):**
  - `app/api/market.py`: intraday bars now include time (`%Y-%m-%d %H:%M`); default ranges scale with interval (1m→7d, 1h→60d, daily→730d) so the frontend/API can't request 730d of 1m.
  - `modules/paper_trading/service.py`: new `replay_trades(store, user_id, fills)` (queued historical prices → MARKET fills through the normal order path, balance/position rules enforced); `reset_account(user_id, capital)` accepts custom capital.
  - `app/api/paper.py`: new `POST /api/paper/replay` — backtest on chosen interval → reconstruct entry/exit fills (entry derived from trade pnl+fees) → resets paper account to `initial_capital` and replays → returns fills/round_trips/account/metrics.
  - **Bug fixed (backtest sizing):** `_sizing` pct mode floored to 0 shares on high-price symbols (BTC ~$60k with 10% of 100k) → no trades ever. Now buys 1 share if the allocation can't afford one. This silently affected ALL pct backtests on expensive symbols.
  - Frontend: Dashboard has an Interval selector (IN=1d only, US/CRYPTO=1d/1h/1m), chart converts intraday dates to epoch seconds, backtest uses interval-appropriate date ranges, "Replay to Paper" button (login) shows paper equity + return, trade table shows intraday timestamps.
- **Test suite: 131 passing.** Live verified end-to-end: OHLCV BTCUSDT 1m (11085 bars), 1m backtest (225 trades, 0.3473%), paper replay (450 fills, equity 100351.57 = same return), paper account persisted.
- Commit: `3388a42` (AI live), next commit = intraday+replay.

**Next:** Phase 2 — screener 2.0, journal AI review, alerts, no-code builder, Tauri, real VPS deploy. See NEXT-STEPS.md.

## 2026-08-07 — Phase 1 wrap (auth, screener, journal, export, deploy) — "complete it till end"
- **Auth + billing** (`modules/auth_billing/`): `UserStore` (JSON, PBKDF2-hashed passwords, server-side session tokens with 30-day expiry), `AuthService` (register/login/create_subscription/user_for_token — satisfies `AuthService` contract). `/api/auth/*` (register/login/subscribe/me). Pro plan gates (`deps.require_plan("pro")`) on strategy save + AI chat. 13 tests.
- **Screener** (`modules/screener/`): `ScreenerService` (price/volume/1d-5d-1m-3m change, above/below SMA 50/200, sortable). `/api/screener/scan`. 7 tests.
- **Trading journal** (`modules/trading_journal/`): `JournalService` (add/list/delete entries, satisfies `Analytics` contract incl. metrics + equity_curve). `/api/journal/*`. 7 tests.
- **Data export**: `/api/export/csv` (StreamingResponse from Parquet store) + `scripts/export_to_git.py` (CSV tree → local git repo, verified end-to-end: 1 parquet → committed repo). 2 API tests.
- **Frontend**: tabbed PWA — Charts+Backtest (Dashboard), Screener, Paper Trading, Journal + auth/login panel + AI assistant panel (chat/confirm) + CSV export link; pro-gated buttons. `NEXT_PUBLIC_API_URL` support.
- **Deploy**: `frontend/Dockerfile` (standalone), `nginx/nginx.conf` (reverse proxy /api→api, /→frontend), full `docker-compose.yml` (api + frontend + nginx + postgres + redis + data volume), `.env.example` expanded, README run-guide. Docker NOT installed on dev machine → compose config written but must be verified on VPS.
- **Test suite: 124 passing** (`python -m pytest modules app`). Live verified: register→subscribe(pro)→screener(45 scanned, 38 matches)→paper fill→journal→CSV export; frontend :3000 ↔ API :8000.
- Commits: `1fef617` (backend+modules), `8eb45f7` (frontend), `1258aae` (deploy).

**Next:** Phase 2 — intraday (US/Crypto 1m) + paper replay, screener 2.0, journal AI review, alerts, no-code builder, Tauri, real VPS deploy. See NEXT-STEPS.md.

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

## 2026-08-08 - Security sandbox pass (path traversal + misc)
- **Path traversal closed:** new `modules/shared/safety.py` `safe_id()` (charset + `.`/`..` rejection) applied to every file-backed store: trading_journal, alerts, watchlists, screener/scans, education, strategy_engine, paper_trading, and market_data `ParquetStore` (market/interval/symbol). Attacker-controlled ids can no longer escape the data dir.
- **Traversal tests:** `modules/trading_journal/tests/test_store_safety.py` (21 cases) covering all per-user stores + parquet store.
- **Watchlists API 422 bug:** endpoints returned `(dict, 422)` (a malformed 200 body); replaced with `HTTPException(status_code=422)`.
- **Sandbox bug:** `_ast_check` blocked *definitions* of `exit`/`quit`, breaking the StrategyBuilder-generated code that reads an `exit` variable. Name blocking now applies only to Load context; `exit`/`quit` removed (harmless in the restricted worker builtins).
- **No command injection:** only subprocess use is the sandbox worker (fixed argv list, no shell). No secrets in code; `.env` gitignored.
- **Frontend API URL:** `http://localhost:8000` hardcode removed from Admin/Watchlist; centralized `API_URL` export in `lib/api.ts` with same-origin fallback.
- **Tests:** 210 passing (modules + app), frontend typecheck clean.

## 2026-08-08 - Authz completion: journal/paper/assistant login-gated (multi-user isolation)
- **Closed the last per-user authz hole:** journal (entry/list/delete/review), paper (order/account/positions/history/reset/replay) and assistant (chat/confirm) accepted a client-supplied `user_id` (query or body, default `demo`) with no auth. Anyone could read/write any user's journal, paper account, or confirm another user's pending AI action.
- **Fix:** every endpoint now derives `user_id` from the bearer token via `Depends(current_user)` (or `require_plan` for Pro) and uses `user.id`. Client-supplied `user_id` removed from all request models/query params.
- **Frontend:** `lib/api.ts` dropped `user_id` from all payloads; journal/paper/assistant helpers now take `token`; `Paper` got `token`/`user` props; login-required prompts + disabled buttons when logged out.
- **Tests:** updated affected API tests to use tokens; added `test_journal_isolated_per_user`, `test_journal_unauth_401`, `test_paper_endpoints_unauth_401` (+ assistant confirm 401). 213 green.
- **Live verified:** register -> paper order FILLED -> journal add/list -> replay 12 round trips; unauthenticated journal/paper -> 401; a second user sees 0 journal entries.
- **Also:** frontend production build re-verified (build had been blocked by a running standalone server), backend restarted without `--reload`, smoke-test users cleaned from the local data store.

## 2026-08-08 — Paper P0-B/P0-E: chart-native bracket orders + reset-to-any-amount
- **Backend** (`modules/paper_trading/service.py`): new `PaperTraderService.set_levels(user_id, symbol, sl, tp)` — updates SL/TP on an open position (keeps qty/avg/ltp/unrealized, persists). `app/api/paper.py`: new `POST /api/paper/position/levels` (404 when no open position, login-gated); `POST /api/paper/reset` now accepts `?amount=` for reset-to-any-amount (defaults to `DEFAULT_CAPITAL`). `deps.py` re-exports `DEFAULT_CAPITAL`.
- **Frontend** (`components/PaperChart.tsx` new): position chart with candles + draggable SL/TP order lines (via `series.createPriceLine` + pointer-drag mapped through `priceToCoordinate`/`coordinateToPrice`; commit on pointer-up) + right-click context menu (Close Position / Reverse Position). Entry line shown at avg price. Live SL/TP sync from server on each refresh.
- **Paper tab** (`components/Paper.tsx`): embedded `PaperChart`, 5s live refresh of account/positions, drag → `setLevels` → P&L updates live; Reset button now prompts for the target balance; `tf:paper-reset` listener fixed to use a ref (no stale closure). `lib/api.ts`: `setLevels` + optional `amount` on `resetAccount`.
- **Chart.tsx:** fixed custom trade-zone renderer TypeScript errors (`CanvasRenderingTarget2D` type import, `scope.context`, whitespace type predicate, `defaultOptions`) — shading still draws via custom series.
- **Tests:** 5 new service tests (set_levels update/clear/none/persist/trigger-exits) + 3 new API tests (reset amount, position levels, 404 + 401). Full suite **236 green**; frontend `tsc` clean + production build green.
