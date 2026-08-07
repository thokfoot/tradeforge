# trade-forge

Universal backtester + paper trading platform for India (NSE/BSE), US, and Crypto markets.
One subscription replaces 4 tools: Streak (backtest/algo) + Tickertape (research) + Chartink (screeners) + trading journal.

> **Status: Phase 1 build in progress (M1 scaffold done).** Backend foundation committed.

## Repo layout

```
AGENTS.md        <- auto-loaded by opencode at session start (full context)
docs/            <- all planning: plan, roadmap, decisions, progress, next-steps, research
docs/architecture/  <- module design, data layer, costs
docs/product/       <- features, pricing, AI-assistant spec
docs/LEGAL.md       <- compliance notes
app/             <- FastAPI application (thin API layer, wires modules via contracts)
modules/         <- backend modules (each isolated: own folder + contract + tests)
frontend/        <- app UI (React / Next.js / PWA)
data-poc/        <- verified data-source proof-of-concept scripts
```

## Current state

Phase 0 (planning) + Phase 0.5 (data PoC) done. Phase 1 build in progress — milestone order:
M1 scaffold (done) → M2 contracts → M3 India adapter → M4 US/Crypto adapters → M5 backtest core.
See `AGENTS.md` and `docs/NEXT-STEPS.md`.

## Run locally (backend)

```
pip install -r requirements.txt
cp .env.example .env      # edit if needed
uvicorn app.main:app --reload
# http://127.0.0.1:8000/health
```

Docker: `docker compose up --build` (app + postgres + redis).

## Markets & data (Phase 1)

| Market | Coverage | Free source (verified) |
|---|---|---|
| India NSE/BSE | All stocks + Nifty 50, Bank Nifty, indices (daily EOD) | `nse-archives` bhavcopy |
| US | All stocks (daily EOD) | yfinance (Stooq dead) |
| Crypto | Major coins (daily; intraday free) | Binance public API + vision archives |

Daily data = Phase 1. Intraday: crypto/US Phase 2, India Phase 3.
