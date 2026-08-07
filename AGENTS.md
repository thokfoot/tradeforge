# trade-forge — Agent Memory / Context File

> This file is AUTO-LOADED at the start of every opencode session.
> It is the single source of truth for "where are we and what is next."
> Update it at the END of every working session (with PROGRESS.md and NEXT-STEPS.md).

## What is this project

A **universal backtester + paper trading platform** for retail traders.
One subscription replaces 4 tools (Streak + Tickertape + Chartink + trading journal).
Markets covered: **India (NSE/BSE — stocks, Nifty 50, Bank Nifty, all indices), US stocks, Crypto.**
Free data sources at launch, provider-swappable architecture. Later: options/F&O + India intraday.

- Status: **Phase 1 COMPLETE (M1–M10 + wrap: auth/billing, screener, journal, data export, deploy config). 124 tests green, live verified. Next: Phase 2.**
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

## Current phase (Phase 0 + 0.5) — DONE items

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

## What is NEXT (see docs/NEXT-STEPS.md for detail)

Phase 2:
1. **Intraday** — US/Crypto 1m bars + minute-level paper replay (Binance pagination + yfinance 1m limits known)
2. **Screener 2.0** — watchlists, more indicators, fundamental filters
3. **Journal AI review** — Gemini reads journal entries and gives feedback
4. **Alerts** — price/indicator push + in-app
5. **No-code strategy builder** (visual blocks)
6. **Tauri desktop** wrapper + notifications
7. **Real deployment** — run `docker compose up --build` on a VPS, domain + HTTPS (compose config ready, not yet tested on server; Docker not installed on dev machine)

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
- Data backfill: `python scripts/backfill_india.py --symbols RELIANCE TCS --years 2 --indices`.
- Live smoke (data → backtest): `python scripts/smoke_backtest.py`.
- Export store to user's own git: `python scripts/export_to_git.py --repo C:/my-data-backup`.
- API surface: `/health`, `GET /api/symbols?market=`, `GET /api/ohlcv/{symbol}`, `POST /api/backtest`, `/api/paper/*` (order/account/positions/history/reset), `/api/strategies/*` (save=Pro/validate/versions), `/api/assistant/*` (chat=Pro/confirm), `/api/auth/*` (register/login/subscribe/me), `/api/screener/scan`, `/api/journal/*`, `/api/export/csv`.
- Env: `GEMINI_API_KEY` enables the real AI chat; `DATA_DIR` roots Parquet + accounts + strategies + auth + journal.
- Auth model: JSON session store (PBKDF2 password hashes, server-side tokens, 30-day expiry). Pro plan gates: strategy save + AI chat. Postgres/Redis in compose for future use.
- Note: NSE bhavcopy = 1 request/trading day (slow for long ranges — run backfill once, store is Parquet).
- Note: port 8123 on this machine is used by a local `socksproxy` service — don't bind the API there.
- Note: Docker is NOT installed on the dev machine — compose config is written but un-tested; verify on the VPS.
- Python 3.11.8 + git on this machine; Node 22 + npm 10 for the frontend.

## Owner / stakeholder facts

- Solo founder, building without hiring. Lots of time, very little money.
- Prefers simple, non-technical explanations. Wants everything "folder-wise, module-wise, traceable."
- Languages: Hinglish (Hindi/English mix). Documentation is English (technical clarity) — explanations to owner in simple Hinglish.
- Language convention: no code comments unless asked. Keep docs factual and scannable.

## Disclaimers (must live in the product)

- "Educational use only", "past performance does not guarantee future results", risk warnings on every results page.
- Paper trading only — AI/agent never places real orders. (Docs/LEGAL.md)
