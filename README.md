# trade-forge

Universal backtester + paper trading platform for India (NSE/BSE), US, and Crypto markets.
One subscription replaces 4 tools: Streak (backtest/algo) + Tickertape (research) + Chartink (screeners) + trading journal.

> **Status: Phase 1 (M1–M10) complete.** Backend + API + Next.js PWA frontend, 124 tests green, live verified.
> ⚠️ Educational use only — paper trading, no real orders.

## Repo layout

```
AGENTS.md        <- auto-loaded by opencode at session start (full context)
docs/            <- all planning: plan, roadmap, decisions, progress, next-steps, research
app/             <- FastAPI application (thin API layer, wires modules via contracts)
modules/         <- backend modules (each isolated: own folder + contract + tests)
frontend/        <- app UI (React / Next.js 16 / PWA / TradingView lightweight-charts)
scripts/         <- CLI: backfill_india, smoke_backtest, export_to_git
nginx/           <- reverse proxy for docker deployment
data-poc/        <- verified data-source proof-of-concept scripts
```

## Features (Phase 1)

- **Charts + backtest** — candlesticks (lightweight-charts), event-driven no-look-ahead engine, realistic Indian cost model (brokerage/STT/GST/SEBI/stamp/slippage), full metrics (CAGR/Sharpe/Sortino/MDD/win-rate/PF/Calmar), reproducible `run_hash`.
- **Screener** — technical filters (price, volume, 1d/5d/1m/3m change, above/below SMA 50/200), sorts by 1m gain.
- **Paper trading** — market/limit orders, positions, trade history, resettable ₹1L virtual account, live quotes.
- **Journal** — note/rating/lesson/tags per trade, per-user.
- **AI assistant (Pro)** — Gemini Flash (free tier) teacher + strategy generator; validates generated code in a sandbox; every action confirmed. Set `GEMINI_API_KEY`.
- **Auth + billing** — email+password, free/pro plans (freemium), pro-gated features.
- **Data export** — CSV download per symbol + `scripts/export_to_git.py` ("export my data to my own git").
- **PWA** — installable on mobile + Windows, offline-capable shell.

## Markets & data (Phase 1)

| Market | Coverage | Free source (verified) |
|---|---|---|
| India NSE/BSE | All stocks + Nifty 50, Bank Nifty, indices (daily EOD) | `nse-archives` bhavcopy |
| US | Popular 45 curated (daily EOD) | yfinance (Stooq dead) |
| Crypto | All USDT pairs (daily) | Binance public API |

## Run locally

Backend (Python 3.11+):

```
pip install -r requirements.txt
cp .env.example .env          # edit DATA_DIR, add GEMINI_API_KEY to enable AI chat
uvicorn app.main:app --reload
# http://127.0.0.1:8000/health
```

Frontend (Node 22+):

```
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
# http://localhost:3000
```

Backfill some data first (NSE is 1 req/trading day — run once):

```
python scripts/backfill_india.py --symbols RELIANCE TCS --years 2 --indices
python scripts/smoke_backtest.py        # live data -> backtest end-to-end
python scripts/export_to_git.py --repo C:/my-data-backup   # export store to your own git
```

## Deploy (Docker)

```
cp .env.example .env          # set GEMINI_API_KEY, NEXT_PUBLIC_API_URL=
docker compose up --build
# http://<server>:80  (nginx -> / = frontend, /api = backend; postgres + redis included)
```

## Tests

```
python -m pytest modules app   # 124 tests
cd frontend && npm run build   # typecheck + production build
```

## API surface

`/health` · `GET /api/symbols?market=` · `GET /api/ohlcv/{symbol}` · `POST /api/backtest`
· `POST /api/paper/order` · `GET /api/paper/{account,positions,history}` · `POST /api/paper/reset`
· `POST /api/strategies/save` (Pro) · `GET /api/strategies/{id}/versions`
· `POST /api/assistant/chat` (Pro) · `POST /api/assistant/confirm`
· `POST /api/auth/{register,login,subscribe}` · `GET /api/auth/me`
· `POST /api/screener/scan` · `POST /api/journal/entry` · `GET /api/journal` · `DELETE /api/journal/{id}`
· `GET /api/export/csv`
