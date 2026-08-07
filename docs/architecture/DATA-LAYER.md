# Data Layer Design

## Goals
- One normalized market-data interface for the whole app.
- Providers are **pluggable** — start free, upgrade later with zero app changes.
- India + US + Crypto, daily from Phase 1; intraday phased.
- Storage cheap: Parquet + compression; popular symbols preloaded, others on-demand.
- Data versioned → reproducible backtests.

## Normalized OHLCV schema (canonical)
```
symbol        TEXT        -- canonical id (e.g., NSE:RELIANCE, US:AAPL, CRYPTO:BTCUSDT)
market        TEXT        -- 'IN' | 'US' | 'CRYPTO'
interval      TEXT        -- '1m','5m','15m','1h','1d', ...
ts            TIMESTAMP   -- bar open time (UTC for US/crypto; IST normalized for India)
open/high/low/close DOUBLE
volume        DOUBLE
adjusted      BOOL        -- adjusted for splits/dividends where provider supplies it
source        TEXT        -- which provider fetched this row (audit)
source_ts     TIMESTAMP   -- when we fetched it
```
All providers MUST map into this schema. This is the contract.

## Provider adapters (Phase 1 targets — VERIFIED 2026-08-07)
| Market | Primary | Fallback | Notes |
|---|---|---|---|
| India (NSE/BSE) | `nse-archives` (PyPI, MIT, active) | `nsepython` | ✅ verified. bhavcopy = daily per-date file (all stocks, OHLC+volume+delivery); indices file (163 indices incl. Nifty 50, P/E, volume, turnover). See findings below |
| US | **yfinance** (Stooq was 404/dead) | Polygon (paid, later) | ✅ verified. Daily full history (~10y+), 1h = 1yr, 1m = only ~last week. Unofficial/ToS gray → licensed upgrade later |
| Crypto | Binance public API | CoinGecko (metadata/lookup) | ✅ verified. Daily + 1m free; `data.binance.vision` monthly archives for bulk deep history |

Upgrade path (later): Financial Modeling Prep / TwelveData (US+fundamentals), licensed NSE vendor (India intraday), Polygon (US intraday).

## Storage strategy
- **Hot cache:** Redis for recent/quotes + popular symbols.
- **Cold store:** Parquet files partitioned by `market/symbol/interval/year`. Postgres holds symbol master + metadata + pointers.
- **Popular symbols always-ready:** India (Nifty 50 + F&O ~200 + indices), US (top ~500 by volume), crypto (major ~50 pairs). Preload via scheduled job.
- **On-demand fetch:** any other symbol requested by a customer → fetch from provider → normalize → cache/store. Same UX for the customer; we just save money.
- **Intraday:** start with crypto (free) Phase 2; US cheap/free Phase 2; India intraday Phase 3 (paid archive, ~₹5–15k one-time, verify licensing).

## Data quality rules
- Corporate actions: prefer provider's adjusted prices; else store raw + adjustment log. (India splits/bonuses are common — must not be ignored.)
- Holiday/weekend gaps: return last trading day, never an error.
- Look-ahead & survivorship bias: fundamentals phase-later; document in LEGAL.md. For backtests, only use data available at bar close (no future bars).
- Symbol mapping layer: NSE vs BSE vs Yahoo vs Binance ticker formats resolved centrally in the adapter + symbol master table.

## Data versioning (reproducibility)
- Each ingestion run tagged with a `data_version`.
- Backtest records `data_version` in its result hash (see ARCHITECTURE.md) → any result is reproducible.

## Data PoC checklist (Phase 0.5) — DONE 2026-08-07
- [x] `nse-archives`: fetch RELIANCE + NIFTY ~10 days; confirm fields, limits, adjust behavior
- [x] US: Stooq fetch (FAILED — 404 on all symbols) → yfinance verified instead
- [x] Binance: fetch BTCUSDT 1d + 1m klines (limit 1000); no auth needed; `data.binance.vision` monthly archive works (HTTP 200)
- [x] Record findings in RESEARCH.md + this file; lock Phase-1 provider per market

## Verified findings (2026-08-07, scripts in `data-poc/`)

### India — `nse-archives` ✅
- `nse.get("capital_market", "equities_sme", "sec_bhavdata_full", date)` → bhavcopy: **3287 rows** (all NSE stocks) for a trading day. Fields: SYMBOL, SERIES, PREV_CLOSE, OPEN/HIGH/LOW/CLOSE_PRICE, AVG_PRICE, TTL_TRD_QNTY, TURNOVER_LACS, NO_OF_TRADES, DELIV_QTY, DELIV_PER.
- `nse.get("capital_market", "indices", "ind_close_all", date)` → **163 indices** incl. Nifty 50, Nifty Next 50, Nifty 100. Fields: Open/High/Low/Close Index Value, Points Change, %, Volume, Turnover (Cr), P/E, P/B, Div Yield.
- Works for past dates (2026-08-06 OK from 2026-08-07). History = one request per trading day → backfill ~250/day/yr. Thread + cache.
- **No split/dividend adjustment info in bhavcopy** (raw prices) → need an adjustment policy/mechanism for India (research later; option: maintain corporate-action log from NSE announcements).
- RELIANCE sample row confirmed (CLOSE 1325.0, volume 20.3M).

### US — yfinance (Stooq FAILED)
- **Stooq** `https://stooq.com/q/d/l/?s=aapl.us&i=d` → **HTTP 404** on all symbol variants (`aapl`, `aapl.us`, `^spx`, `spy.us`). Treat Stooq as unavailable.
- **yfinance** ✅: `Ticker("AAPL").history(period=...)` → OHLC + Volume + **Dividends + Stock Splits** (adjusted-friendly). AAPL 10y daily = 2514 rows (2016→2026). 1h = 1yr (1741 rows). **1m = only last ~5–7 days** (Yahoo limit) → NOT enough for 1m backtesting free; paid later (Polygon).
- Unofficial (Yahoo ToS gray) → flag licensed upgrade (FMP/TwelveData) when revenue allows.

### Crypto — Binance ✅
- `api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000` → 1000 bars/call, paginate with `startTime`. No auth needed.
- 1m klines work (1000 bars/call, paginate).
- **`data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-YYYY-MM.zip`** → deep history free (Jan 2020 tested, HTTP 200, ~2.2MB). Bulk download for intraday archives.

## LOCKED Phase-1 providers
| Market | Provider | Interval (Phase 1) |
|---|---|---|
| India | `nse-archives` bhavcopy | daily EOD |
| US | yfinance | daily EOD (1h available for Phase 2) |
| Crypto | Binance API + vision archives | daily (+ 1m for Phase 2 free) |
