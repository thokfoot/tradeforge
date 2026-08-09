# trade-forge — Agent Memory / Context File

> This file is AUTO-LOADED at the start of every opencode session.
> It is the single source of truth for "where are we and what is next."
> Update it at the END of every working session (with PROGRESS.md and NEXT-STEPS.md).

## What is this project

A **universal backtester + paper trading platform** for retail traders.
One subscription replaces 4 tools (Streak + Tickertape + Chartink + trading journal).
Markets covered: **India (NSE/BSE — stocks, Nifty 50, Bank Nifty, all indices), US stocks, Crypto.**
Free data sources at launch, provider-swappable architecture. Later: options/F&O + India intraday.

- Status: **Phase 3 complete. Local release candidate verified with 236 tests green. Tauri .exe built. Education + Watchlists + Onboarding + Full Hindi i18n + Admin dashboard all done. India/US/Crypto data and index filters are local. Security hardening pass done (path traversal closed, authz on journal/paper/assistant, sandbox AST fix). Paper trading upgraded (chart-native bracket orders: draggable SL/TP lines + right-click Close/Reverse, reset-to-any-amount). Only optional deeper history and VPS launch remain.**
- Language/stack: Python (FastAPI) backend, React (Next.js + PWA) frontend, Tauri (Windows later), Postgres + Redis + Parquet, Docker. Module folders use underscores (`modules/market_data`, `modules/backtest_engine`).
- Business model: Freemium. Pro target ₹199/mo (₹99–199). 10 customers × ₹199 covers server; 25 covers everything.
- Server: cloud VPS (start Oracle free tier / ₹500-mo Hetzner). NOT the owner's home PC.

## Project location & structure

- Root: `C:\trade-forge` (Windows). Git repo initialized here.
- `docs/` — ALL planning (see below). `modules/` — backend modules. `frontend/` — UI.

## Module architecture (CRITICAL — owner's #1 requirement)

> Owner's hard rule: **changing one module/feature must NEVER disturb any other feature (not even 0.1%).**
> They have seen AI projects where fixing one thing breaks another. Prevent via:

1. **Contracts first.** Modules talk ONLY through interfaces in `modules/shared/contracts/`. No module ever touches another module's internals.
2. **Tests per module.** Every module ships with its own tests. Run the suite after ANY change — it instantly reports what broke.
3. **No shared global state.** Modules never mutate each other's data.
4. **AI module runs as an isolated process/service** — a crash or change there never affects the rest of the app.
5. **Provider adapters** for anything swappable (data providers, AI providers) — swap = config change, zero impact elsewhere.

Rule of thumb for every change: edit inside the module folder only + run tests + update its README. Nothing outside.

## Current phase — DONE items

- [x] Market + competitor + data-source research (see `docs/RESEARCH.md`)
- [x] Business/product decisions locked (see `docs/DECISIONS.md`)
- [x] Cost model locked (see `docs/architecture/COSTS.md`)
- [x] Modular architecture + isolation rules defined (see `docs/architecture/ARCHITECTURE.md`)
- [x] Data layer design + verified findings (see `docs/architecture/DATA-LAYER.md`)
- [x] Feature/pricing/AI-assistant specs (see `docs/product/`)
- [x] Legal notes (see `docs/LEGAL.md`)
- [x] Repo + docs + module skeleton committed
- [x] **Data PoC (Phase 0.5): all 3 markets verified** — India=nse-archives ✅, US=yfinance ✅ (Stooq dead), Crypto=Binance ✅. Scripts in `data-poc/`. Providers locked.
- [x] **Phase 1 M1–M10 (full product MVP)** — scaffold, contracts (approved), 3 data adapters, backtest engine, data/backtest API, paper trading, strategy storage + sandbox, AI assistant MVP, Next.js PWA frontend. 86 tests green.
- [x] **Phase 1 wrap** — auth + billing (register/login/subscribe, PBKDF2, session tokens, pro plan gates), screener (technical filters over store), trading journal (Analytics contract), data export (CSV + `scripts/export_to_git.py`), deploy config (compose + nginx + standalone frontend Dockerfile). 124 tests green.
- [x] **AI assistant LIVE** — `GEMINI_API_KEY` in `.env` → `settings.gemini_api_key`; model `gemini-flash-latest`; Settings `extra="ignore"` so extra env vars don't break startup. Live Hinglish replies verified.
- [x] **Phase 2 #1 Intraday + replay** — 1m/1h bars with timestamps, interval-scaled default ranges, `POST /api/paper/replay` (backtest → reconstruct fills → replay into paper ledger), Dashboard interval picker + Replay-to-Paper, pct-sizing min-1-share fix.
- [x] **Phase 2 #2 Screener 2.0** — RSI(14)/Bollinger %B/vol-ratio/SMA20/MACD indicators + filters + sort; `SavedScan`+`ScanStore` + auth-gated API (save/list/delete/run); frontend filters + saved-scan chips. 141 tests green.
- [x] **Phase 2 #3 Journal AI review** — `AIAssistant.review_journal(user_id, entries)` contract + service method (last-30 entries → Hinglish patterns/strengths/risks/improvements, provider-error fallback); `POST /api/journal/review` (Pro-gated); Journal tab "🤖 AI Review my Journal (Pro)" button. 146 tests green, live verified (real Gemini feedback on actual AAPL/TSLA entries).
- [x] **Phase 2 #4 Alerts** — new `modules/alerts/`: `AlertRule`/`AlertNotification` contracts + `AlertService` (create/list/delete, PRICE or RSI(14) ABOVE/BELOW one-shot rules, in-app notifications, `check_user`/`check_all`); `/api/alerts/*` (create/list/delete/notifications/clear/check — login-gated); background loop in app lifespan (config-gated `ALERTS_ENABLED`); Alerts tab in frontend. 161 tests green, live verified (AAPL price rule fired on real quote 312.96, RSI rule realistic).
- [x] **Phase 2 #5 No-code strategy builder** — new `modules/strategy_builder/` (`StrategyBuilder` pure code generator: indicator blocks close/open/high/low/volume/sma/ema/rsi × above/below × threshold or vs-indicator, AND/OR joins, stateful entry/exit machine). Generated code runs in the sandbox too (no imports, top-level names only). `POST /api/builder/generate` (Pro) → code + sandbox validation. Frontend Strategy Builder tab (blocks + inline backtest runner). 174 tests green, live verified (RSI-pullback spec → AAPL daily backtest 10 trades +4.46%).
- [x] **Paper P0-B/P0-E — chart-native bracket orders + reset-to-any-amount** — `PaperTraderService.set_levels()` + `POST /api/paper/position/levels` (404 on no position); `POST /api/paper/reset?amount=`. New `components/PaperChart.tsx`: candles + draggable SL/TP price lines (drag → `setLevels` → live P&L) + right-click Close/Reverse. Paper tab: chart embedded, 5s live refresh, Reset prompts for target balance. Chart.tsx custom trade-zone renderer type fixes. **236 tests green** (`python -m pytest modules app`).

## What is NEXT (see docs/NEXT-STEPS.md for detail)

Phase 2:
1. ~~Intraday + replay~~ **DONE** (1m/1h bars, minute backtest + `POST /api/paper/replay`, frontend interval picker)
2. ~~Screener 2.0~~ **DONE** (RSI/BB/vol-ratio/MACD filters, saved scans per user, login-gated)
3. ~~Journal AI review~~ **DONE** (Gemini reads journal entries → Hinglish patterns/feedback via `POST /api/journal/review`, Pro-gated)
4. ~~Alerts~~ **DONE** (price + RSI one-shot rules, in-app notifications, `/api/alerts/*`, background loop behind `ALERTS_ENABLED`)
5. ~~No-code strategy builder~~ **DONE** (visual blocks → sandbox-validated strategy code via `POST /api/builder/generate`, Pro)
6. ~~Tauri desktop~~ **DONE** — config + Rust backend written (`frontend/src-tauri/`), notification plugin wired, Alerts → native OS notifications via `@tauri-apps/plugin-notification`. Cannot build yet: Rust not installed on dev machine.
7. ~~Real deployment~~ **DONE** — `scripts/deploy.sh` (--setup, --ssl DOMAIN, update), `nginx/nginx-ssl.conf` (HTTPS + Let's Encrypt), `docker-compose.yml` (443 + certbot volume + NGINX_CONF env var), `.env.example` VPS checklist. Untested: Docker not on dev machine.

### Phase 3 — Polish & launch
1. ~~Install Rust~~ **DONE** — `winget install Rustlang.Rustup` + MSYS2 MinGW toolchain (`C:\msys64\mingw64\bin`). Tauri .exe built: `C:\trade-forge\frontend\src-tauri\target\release\trade-forge.exe` (21.8 MB).
2. ~~Education~~ **DONE** — new Learn tab with 12 in-app lessons across 6 sections (Getting Started, Backtesting, Indicators, Paper Trading, Strategy Builder, Risk Management). English/Hinglish language toggle (EN/HI buttons). Content in `frontend/lib/lessons.ts`, component `frontend/components/Education.tsx`.
3. ~~Demo account~~ **DONE** — `scripts/seed_demo.py`: creates `demo@tradeforge.in` / `tradeforge123` Pro account with 6 sample journal entries (AAPL, TSLA, RELIANCE, BTCUSDT).
4. ~~Data check~~ **DONE** — store is 1.8 MB (56 files), US symbols have decent coverage (43 parquet files), smoke test passes.
5. ~~Postgres migration~~ **DONE** — SQLAlchemy models (`modules/shared/models.py`: 15 tables — users, sessions, strategies, journal_entries, alert_rules, alert_notifications, saved_scans, education_progress, paper_accounts, paper_positions, paper_orders, paper_trades). PG-backed store variants (`modules/shared/pg_stores.py`) matching all 7 JSON store interfaces. Config flag `DB_BACKEND=postgres` switches deps.py to use PG stores. Migration script `scripts/migrate_to_pg.py` copies JSON→Postgres. `init_db()` auto-creates tables on startup. Default is `json` (backward compatible — no DB needed).
6. **VPS test** — run `bash scripts/deploy.sh --setup` on a real cloud VPS with Docker, set `DB_BACKEND=postgres`, verify all services.

### Local release candidate — DONE

- Backend production process verified without reload on port 8000.
- Frontend standalone production server verified on port 3000; `npm start` runs `node .next/standalone/server.js`.
- India local data: 3,462 NSE stock/index files after a 30-day all-stock backfill; NIFTY 50, NIFTY BANK, NIFTY TOTAL MARKET, Nifty 50 constituents, and Bank Nifty constituents have a 90-day window.
- US and Crypto local data verified; local development avoids remote gap fetching when local Parquet data exists.
- All-market smoke tests, India screener, India backtest, India paper order/reset, frontend response, and 179 automated tests pass.

## Key decisions (short version — full reasons in docs/DECISIONS.md)

- Git per customer → **reimagined**: git stores strategy code + "export my data to my git" feature. Runtime data in Postgres/Parquet. NO git-as-primary-database.
- Home PC as server → **NO**. Cloud VPS (₹0–500/mo).
- All markets daily data in Phase 1 (India+US+Crypto). Intraday: crypto/US Phase 2, India intraday Phase 3 (paid archive ~₹5–15k one-time).
- Storage: popular symbols always-ready, rest fetched on-demand.
- AI assistant (3-in-1 teacher/listener/doer, voice + any language) — start with **Gemini Flash free tier API**, provider-adapter pattern (Gemini ↔ Ollama self-host ↔ paid later). Owner's Jio Gemini Pro is for personal use only, not an API.
- Pricing: Freemium. No "cheapest in market" race — compete on bundling + realism + teaching.
- App: Web + PWA (installable mobile + Windows, ₹0 store fees). Native apps Phase 3.
- Backtest realism (slippage + full Indian cost model: brokerage/STT/GST/SEBI/stamp) is the #1 trust moat.

## Commands / tooling

- Tests: `python -m pytest modules app` (from repo root). Run after ANY module change.
- Backend: `uvicorn app.main:app --reload` → `/health` (dev). Full stack: `docker compose up --build`.
- Frontend: `cd frontend && npm run dev` (uses `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`). Production: `npm run build && npm run start` (or the standalone Dockerfile).
- Local restart helper: `powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1` automatically stops only old Trade Forge servers and opens fresh backend/frontend windows. Add `-Development` for Next dev mode.
- Tauri dev (needs Rust installed): `cd frontend && npm run tauri dev`. Build: `npm run tauri build`.
- Data backfill: `python scripts/backfill_india.py --symbols RELIANCE TCS --days 90 --indices` or `--all-stocks --days 30 --indices` (batch-saves; use `--years 2` for deeper history).
- Live smoke (data → backtest): `python scripts/smoke_backtest.py`.
- Export store to user's own git: `python scripts/export_to_git.py --repo C:/my-data-backup`.
- API surface: `/health`, `GET /api/symbols?market=`, `GET /api/ohlcv/{symbol}`, `POST /api/backtest`, `/api/paper/*` (order/account/positions/history/reset?amount=/position/levels/replay — login-gated, user from token), `/api/strategies/*` (save=Pro/validate/versions), `/api/assistant/*` (chat=Pro/confirm — login-gated), `/api/auth/*` (register/login/subscribe/me), `/api/screener/scan` + `/api/screener/scans/*` (save/list/delete/run — login-gated), `/api/journal/*` (entries + **review**=Pro), `/api/alerts/*` (create/list/delete/notifications/clear/check — login-gated), `/api/builder/generate` (no-code strategy code, Pro), `/api/export/csv`, `/api/watchlists` (add/remove/list — login-gated).
- Env: `GEMINI_API_KEY` enables the real AI chat (`GEMINI_MODEL` default `gemini-flash-latest`); `DATA_DIR` roots Parquet + accounts + strategies + auth + journal + screener + alerts. `ALERTS_ENABLED=1` + `ALERT_CHECK_INTERVAL_SECONDS` start the alerts background worker (off by default). `.env` may contain frontend vars (`NEXT_PUBLIC_API_URL`) — backend Settings ignores extras.
- Auth model: JSON session store (PBKDF2 password hashes, server-side tokens, 30-day expiry). **All per-user endpoints (journal, paper, assistant, alerts, scans, watchlists) derive `user_id` from the bearer token via `current_user` — never trust a client-supplied `user_id`.** Pro plan gates: strategy save + AI chat. Postgres/Redis in compose for future use.
- Note: NSE bhavcopy = 1 request/trading day (slow for long ranges — run backfill once, store is Parquet).
- Note: port 8123 on this machine is used by a local `socksproxy` service — don't bind the API there.
- Note: Docker is NOT installed on the dev machine — compose config + deploy script written but un-tested; verify on the VPS.
- Note: Rust IS installed (1.97.1, GNU toolchain). MinGW linker at `C:\msys64\mingw64\bin` — add to PATH before `cargo` commands. Tauri builds confirmed working. Run: `$env:Path += ";C:\msys64\mingw64\bin"` before `npm run tauri dev`.
- Python 3.11.8 + git on this machine; Node 22 + npm 10 for the frontend.

## Owner / stakeholder facts

- Solo founder, building without hiring. Lots of time, very little money.
- Prefers simple, non-technical explanations. Wants everything "folder-wise, module-wise, traceable."
- Languages: Hinglish (Hindi/English mix). Documentation is English (technical clarity) — explanations to owner in simple Hinglish.
- Language convention: no code comments unless asked. Keep docs factual and scannable.

## Disclaimers (must live in the product)

- "Educational use only", "past performance does not guarantee future results", risk warnings on every results page.
- Paper trading only — AI/agent never places real orders. (Docs/LEGAL.md)
