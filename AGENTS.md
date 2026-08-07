# trade-forge — Agent Memory / Context File

> This file is AUTO-LOADED at the start of every opencode session.
> It is the single source of truth for "where are we and what is next."
> Update it at the END of every working session (with PROGRESS.md and NEXT-STEPS.md).

## What is this project

A **universal backtester + paper trading platform** for retail traders.
One subscription replaces 4 tools (Streak + Tickertape + Chartink + trading journal).
Markets covered: **India (NSE/BSE — stocks, Nifty 50, Bank Nifty, all indices), US stocks, Crypto.**
Free data sources at launch, provider-swappable architecture. Later: options/F&O + India intraday.

- Status: **Phase 1 M1–M10 DONE (full backend + frontend MVP, 86 tests green, live API + PWA verified). Next: Phase 1 wrap (auth, deploy) → Phase 2.**
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

## What is NEXT (see docs/NEXT-STEPS.md for detail)

Phase 1 wrap + Phase 2:
1. **Phase 1 wrap** — auth/billing (M10b), `docker compose` deploy to VPS, seed data backfill, README run-guide
2. **Phase 2** — intraday (US/Crypto 1m) + live-ish paper replay, screener, data export to git, trading journal, Tauri desktop

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
- Frontend: `cd frontend && npm run dev` (uses `NEXT_PUBLIC_API_URL`, default `http://localhost:8000`). Production: `npm run build && npm run start`.
- Data backfill: `python scripts/backfill_india.py --symbols RELIANCE TCS --years 2 --indices`.
- Live smoke (data → backtest): `python scripts/smoke_backtest.py`.
- API surface: `/health`, `GET /api/symbols?market=`, `GET /api/ohlcv/{symbol}`, `POST /api/backtest`, `/api/paper/*` (order/account/positions/history/reset), `/api/strategies/*` (save/validate/versions), `/api/assistant/*` (chat/confirm).
- Env: `GEMINI_API_KEY` enables the real AI chat; `DATA_DIR` roots Parquet + accounts + strategies.
- Note: NSE bhavcopy = 1 request/trading day (slow for long ranges — run backfill once, store is Parquet).
- Note: port 8123 on this machine is used by a local `socksproxy` service — don't bind the API there.
- Python 3.11.8 + git on this machine; Node 22 + npm 10 for the frontend.

## Owner / stakeholder facts

- Solo founder, building without hiring. Lots of time, very little money.
- Prefers simple, non-technical explanations. Wants everything "folder-wise, module-wise, traceable."
- Languages: Hinglish (Hindi/English mix). Documentation is English (technical clarity) — explanations to owner in simple Hinglish.
- Language convention: no code comments unless asked. Keep docs factual and scannable.

## Disclaimers (must live in the product)

- "Educational use only", "past performance does not guarantee future results", risk warnings on every results page.
- Paper trading only — AI/agent never places real orders. (Docs/LEGAL.md)
