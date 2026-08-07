"""Data PoC — India (nse-archives). Throwaway verification script."""
import sys
from datetime import date, timedelta

from nsedata import nse

print("nse-archives imported OK")


def fetch_with_fallback(dates):
    for d in dates:
        try:
            df = nse.get("capital_market", "equities_sme", "sec_bhavdata_full", d.isoformat())
            print(f"\nBHAVCOPY {d.isoformat()}: OK, rows={len(df)}")
            print("columns:", list(df.columns)[:15])
            return df
        except Exception as e:
            print(f"bhavcopy {d.isoformat()} failed: {type(e).__name__}: {str(e)[:120]}")
    return None


dates = [date.today() - timedelta(days=n) for n in range(1, 6)]
df = fetch_with_fallback(dates)

if df is not None:
    for col in df.columns:
        if "SYMBOL" in str(col).upper():
            row = df[df[col] == "RELIANCE"]
            if not row.empty:
                print("\nRELIANCE row (last 3 cols):")
                print(row.iloc[-1].tail(8))
            break

# Indices
for d in dates:
    try:
        idx = nse.get("capital_market", "indices", "ind_close_all", d.isoformat())
        print(f"\nINDICES {d.isoformat()}: OK, rows={len(idx)}")
        print("columns:", list(idx.columns)[:12])
        print(idx.head(3).to_string())
        break
    except Exception as e:
        print(f"indices {d.isoformat()} failed: {type(e).__name__}: {str(e)[:120]}")
