# module: market-data

**Purpose:** Fetch, normalize, store, and serve market data for India (NSE/BSE), US, and Crypto. Provider-agnostic.

**Contract:** `MarketDataProvider` (see `../shared/contracts/README.md`).

**Adapters (Phase 1):**
- India: `nse-archives` (primary), `nsepython` (fallback) — stocks + Nifty 50/Bank Nifty/indices, daily
- US: Stooq (primary), yfinance (fallback) — daily EOD
- Crypto: Binance public API — daily + intraday (free)

**Isolation:** Owns its storage (Parquet + Postgres metadata) exclusively. Others read via contract only. Swapping providers = adding an adapter, zero impact elsewhere.

**Status:** Planning. Next: data PoC (see `docs/NEXT-STEPS.md`) → then implement adapter interface + India adapter.
