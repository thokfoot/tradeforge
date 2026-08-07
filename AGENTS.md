# trade-forge — Agent Memory / Context File

> This file is AUTO-LOADED at the start of every opencode session.
> It is the single source of truth for "where are we and what is next."
> Update it at the END of every working session (with PROGRESS.md and NEXT-STEPS.md).

## What is this project

A **universal backtester + paper trading platform** for retail traders.
One subscription replaces 4 tools (Streak + Tickertape + Chartink + trading journal).
Markets covered: **India (NSE/BSE — stocks, Nifty 50, Bank Nifty, all indices), US stocks, Crypto.**
Free data sources at launch, provider-swappable architecture. Later: options/F&O + India intraday.

- Status: **Phase 0 (planning) + Phase 0.5 (data PoC) DONE. Phase 1 build starts next — repo scaffold, contracts, then India adapter.**
- Language/stack planned: Python (FastAPI) backend, React (Next.js + PWA) frontend, Tauri (Windows later), Postgres + Redis + Parquet, Docker.
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

## What is NEXT (see docs/NEXT-STEPS.md for detail)

Phase 1 build, milestone order:
1. **M1** Repo scaffold — FastAPI + Postgres + Redis + Parquet + Docker (`requirements.txt`, `app/`, `.env`, compose)
2. **M2** Contracts — implement `modules/shared/contracts/` as Python Protocols (get owner approval on names first)
3. **M3** India data adapter — nse-archives → canonical OHLCV → Parquet; symbol master; backfill + on-demand
4. **M4** US (yfinance) + Crypto (Binance) adapters
5. **M5** Backtest engine core (event-driven + Indian cost model + reproducible hash)

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

- No build tooling yet (planning phase). Python 3.9+ and git assumed available on this machine.
- Data PoC is pure Python — check `pip` availability before starting.

## Owner / stakeholder facts

- Solo founder, building without hiring. Lots of time, very little money.
- Prefers simple, non-technical explanations. Wants everything "folder-wise, module-wise, traceable."
- Languages: Hinglish (Hindi/English mix). Documentation is English (technical clarity) — explanations to owner in simple Hinglish.
- Language convention: no code comments unless asked. Keep docs factual and scannable.

## Disclaimers (must live in the product)

- "Educational use only", "past performance does not guarantee future results", risk warnings on every results page.
- Paper trading only — AI/agent never places real orders. (Docs/LEGAL.md)
