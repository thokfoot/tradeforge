# module: screener

**Purpose:** Stock screening — technical + fundamental filters across India, US, and crypto.

**Contract:** uses `MarketDataProvider` (data) — screening logic lives here.

**Phase 1 (basic):** technical filters (price, % change, volume, RSI, MACD, 52w high/low, moving averages) + basic fundamentals (market cap, P/E) where free data allows.

**Later:** saved screens, alerts on screens, real-time scanning.

**Isolation:** Reads data via contract; owns saved-screen preferences only.

**Status:** Planning.
