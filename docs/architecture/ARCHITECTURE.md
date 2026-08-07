# Architecture — Modular Design & Isolation Rules

## Owner's #1 hard requirement

> **Changing one module / feature must NEVER disturb any other feature — not even 0.1%.**
> (Owner has seen AI projects where fixing X breaks Y, then fixing Y breaks Z.)

This document is the contract for how we prevent that. It is not optional.

## The 5 isolation rules (non-negotiable)

1. **Contracts first.** Modules communicate ONLY through interfaces defined in `modules/shared/contracts/`. No module imports or touches another module's internals, database tables, or private functions.
   - Analogy: a wall socket. Rewire the inside of module A freely; module B only ever plugs into the socket.
2. **Tests per module.** Every module ships with its own test suite. After ANY change: run the full suite. It tells you in minutes exactly what (if anything) broke. This is the machine that makes the guarantee real.
3. **No shared global/mutable state.** Modules never write to each other's data. Each owns its storage exclusively (per-module tables/schemas; cross-module data via API calls or events, not direct DB writes).
4. **AI module runs as an isolated process/service.** A crash or change in AI must not affect anything else. Talk to it over the contract interface only.
5. **Provider adapters for anything swappable.** Market data providers and AI providers are plugins behind a single interface. Swapping = config change; zero impact on the rest of the system.

## Change workflow (the rule every session follows)

1. Identify the owning module.
2. Make the change INSIDE that module only (code + its own tests).
3. Run that module's tests + full suite.
4. If a contract/interface changes: bump the contract version; keep the old one working for one release (parallel versions), then migrate consumers explicitly.
5. Update the module README + PROGRESS.md.

## System diagram (target)

```
                      ┌──────────────────────────────────────────┐
                      │  Frontend  (Next.js + lightweight-charts) │
                      │  Web · PWA (mobile+Windows installable)   │
                      └──────────────────┬───────────────────────┘
                                         │ REST / WebSocket
                      ┌──────────────────▼───────────────────────┐
                      │             API Gateway                  │
                      └──┬────┬────┬────┬────┬────┬────┬─────────┘
                         │    │    │    │    │    │    │
   ┌─────────────────────┼────┼────┼────┼────┼────┼────┼─────────────────────┐
   │  auth-billing       │    │    │    │    │    │    │   notifications      │
   │  market-data ───────┘    │    │    │    │    │    │                      │
   │  strategy-engine ────────┘    │    │    │    │    │                      │
   │  backtest-engine ─────────────┘    │    │    │    │                      │
   │  paper-trading ────────────────────┘    │    │    │                      │
   │  analytics ─────────────────────────────┘    │    │                      │
   │  screener ───────────────────────────────────┘    │                      │
   │  education ───────────────────────────────────────┘                      │
   │  ai-assistant  ────────── ISOLATED PROCESS ──────────────────────────────┤
   └───────────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
                 Postgres   Redis      Parquet (object storage)
                 (users,    (cache,     (market data files)
                  trades)    queues)
```

## Tech stack (locked)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python + FastAPI | Best data/finance ecosystem; async; fast to build solo |
| DB | PostgreSQL | Users, strategies, trades, journal |
| Cache/queue | Redis | Caching, worker queues (backtests) |
| Market data files | Parquet (+ compression) | Fast analytics, small storage |
| Backtest engine | Own lean event-driven core (numpy/pandas) | Full control over Indian cost model; no GPL/Commons-Clause engines in a commercial product |
| AI | Gemini Flash (free tier) behind adapter | ₹0, best Hindi/agent quality, switchable (Ollama later) |
| Charts | TradingView lightweight-charts (open source) | Same engine family as TradingView; world-class, free |
| Frontend | React + Next.js + Tailwind | Web + PWA in one codebase |
| Desktop (later) | Tauri | Windows installable, tiny footprint |
| Deployment | Docker + VPS (Oracle free → Hetzner ₹500/mo) | Cheapest reliable |
| Monitoring/backup | Daily automated backups to object storage | Data never lost |

## Module inventory

| Module | Responsibility | Talks to (contracts) |
|---|---|---|
| `auth-billing` | Users, login, subscriptions, payments | Auth contract |
| `market-data` | Provider adapters, normalization, storage, on-demand fetch | MarketDataProvider contract |
| `strategy-engine` | No-code + code strategies, validation, versioning (git) | Strategy contract |
| `backtest-engine` | Event-driven simulation, cost model, metrics, reproducible hashes | BacktestEngine contract |
| `paper-trading` | Live simulation, positions/orders/history, parity scoring | PaperTrader contract |
| `analytics` | Stats, equity curves, journal, reports | Analytics contract |
| `screener` | Technical + fundamental screening | (uses market-data via contract) |
| `education` | Learning content, lessons, quizzes | — |
| `ai-assistant` | Teacher + listener + doer agent; isolated process | AIAssistant contract |
| `notifications` | Alerts: in-app, push | Notification contract |
| `shared/contracts` | **All interfaces — the stable base** | — |

## Reproducibility & traceability (owner's requirement)

- Every backtest run stores a **hash of (strategy code version + data version + parameters)** → any result can be regenerated.
- Strategies are **versioned in git** (per user, branch/tag per version).
- All docs, decisions, and code live in the same repo with history.
- Future: "export my data to my git" for every customer (data ownership).
