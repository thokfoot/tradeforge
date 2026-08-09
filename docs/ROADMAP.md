# Roadmap — Phase-by-phase checklist

Status legend: `[ ]` pending · `[x]` done · `[~]` in progress

## Phase 0 — Planning (DONE)

- [x] Market/competitor research (2026): Streak, Tradetron, TradingView, Tickertape, Sensibull, Backtrex, TradeZella, Chartink
- [x] New-trader requirements by skill level (beginner/intermediate/expert)
- [x] Free data source research (India: nse-archives/nsepython/bhavcopy; US: Stooq/Yahoo; Crypto: Binance)
- [x] Lock business decisions (DECISIONS.md)
- [x] Cost model (COSTS.md)
- [x] Modular architecture + isolation rules (ARCHITECTURE.md)
- [x] Data layer design (DATA-LAYER.md)
- [x] Features / pricing / AI-assistant specs (product/)
- [x] Legal notes (LEGAL.md)
- [x] Repo + docs + module skeleton committed

## Phase 0.5 — Data proof-of-concept (DONE)

- [x] India: fetch 5–10 days EOD via nse-archives
- [x] US: fetch EOD via yfinance
- [x] Crypto: fetch daily + 1m via Binance
- [x] Record working sources → DATA-LAYER.md
- [x] Lock Phase-1 providers: NSE=bhavcopy, US=yfinance, Crypto=Binance

## Phase 1 — Base (8–10 wk) — India + US + Crypto daily

### Backend foundation
- [ ] Repo scaffold: FastAPI + Postgres + Redis + Parquet, Docker, CI placeholder
- [ ] `shared/contracts` interfaces: MarketDataProvider, Strategy, BacktestEngine, PaperTrader, Analytics, AIAssistant, Auth
- [ ] Config/secrets handling (env-based)

### Data layer
- [ ] MarketDataProvider adapters: NSE(India), Stooq(US), Binance(Crypto)
- [ ] Normalized OHLCV schema + storage (Parquet + Postgres metadata)
- [ ] Symbol master + symbol mapping (NSE vs BSE vs Yahoo ticker formats)
- [ ] Popular-symbols preload + on-demand fetch job

### Backtest engine
- [ ] Event-driven core (bar-by-bar), no look-ahead
- [ ] Cost model: brokerage + STT + GST + SEBI + stamp duty (India), fees (US), maker/taker (crypto)
- [ ] Slippage model
- [ ] Order types: market, limit, SL, bracket
- [ ] Metrics: win rate, profit factor, max drawdown, equity curve, R-multiple, expectancy, per-trade log
- [ ] Reproducible backtests (hash of code+data+params) — unique feature

### Paper trading
- [ ] Live price simulation engine, virtual balance (reset option)
- [ ] Positions/orders/history tracking
- [ ] Parity scoring: backtest vs paper vs live expectations

### Charts + screener
- [x] TradingView lightweight-charts integration
- [x] 50+ indicators, multiple timeframes
- [x] Basic technical + fundamental screener
- [x] Watchlists (DONE module + API + tab)

### AI assistant (MVP)
- [x] Gemini Flash free-tier integration (AI provider adapter — Gemini ↔ Ollama later)
- [x] Teacher mode: explain RSI, volume, candlesticks etc. (any language, simple words)
- [x] Listener mode: convert natural language (type or voice) → structured strategy, confirm back in plain words
- [x] Action mode: create strategy → run backtest → show results (paper-only, every step confirmed)
- [ ] Conversation memory per user

### Users, export, billing
- [x] Auth (email+password), user profiles
- [x] "Export my data to my git" feature (owner's data-ownership vision)
- [ ] Daily automatic backups
- [ ] Subscriptions (Razorpay) — basic plans

### Frontend
- [x] Next.js app + PWA (installable mobile + Windows)
- [x] Onboarding wizard for beginners (guided)
- [x] Hinglish/Hindi language toggle (full app)
- [x] Admin/ops dashboard (basic)

## Phase 2 — Speed (6–8 wk) — DONE

- [x] Crypto intraday backtesting (Binance free)
- [x] US intraday (free/cheap source)
- [x] Trading journal module
- [x] Alerts (price/indicator, push/in-app)
- [x] No-code strategy builder (visual)
- [x] Education content + learning paths
- [x] Full Hindi UI

## Phase 3 — Full power (8–12 wk)

- [ ] India intraday (bulk archive purchase ~₹5–15k one-time; verify licensing)
- [ ] Options/F&O backtesting (paid data source)
- [ ] Walk-forward + Monte Carlo
- [ ] Expert API access
- [x] Native mobile + Windows apps (Tauri .exe built 21.8 MB)
- [ ] Community/marketplace (legal review first)

## Ideas backlog (future)

- Strategy templates library (ICT, ORB, trend-following, mean reversion)
- Parameter optimization grid
- Copy/social trading (legal review first)
- Live market scanning (real-time scanners)
