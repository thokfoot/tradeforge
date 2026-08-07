"""Data PoC — US depth + intraday limits (yfinance)."""
import yfinance as yf
import pandas as pd

pd.set_option("display.width", 150)

t = yf.Ticker("AAPL")
df = t.history(period="10y", interval="1d")
print(f"AAPL 10y daily: rows={len(df)}  range={df.index.min().date()} -> {df.index.max().date()}")

try:
    m = t.history(period="5d", interval="1m")
    print(f"AAPL 1m (last 5d): rows={len(m)}  first={m.index.min()} last={m.index.max()}")
except Exception as e:
    print("1m fetch failed:", str(e)[:120])

try:
    h = t.history(period="1y", interval="1h")
    print(f"AAPL 1h (1y): rows={len(h)}  range={h.index.min()} -> {h.index.max()}")
except Exception as e:
    print("1h fetch failed:", str(e)[:120])
