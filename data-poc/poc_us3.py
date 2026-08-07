"""Data PoC — US (yfinance fallback). Throwaway verification script."""
import yfinance as yf
import pandas as pd

pd.set_option("display.width", 150)

for sym in ["AAPL", "SPY"]:
    try:
        t = yf.Ticker(sym)
        df = t.history(period="2y", interval="1d")
        print(f"\n{sym}: OK rows={len(df)}")
        print("cols:", list(df.columns))
        print(df.tail(2).to_string())
    except Exception as e:
        print(f"{sym}: FAIL {type(e).__name__}: {str(e)[:150]}")
