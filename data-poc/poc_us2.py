"""Data PoC — US (Stooq EOD) variations test."""
import io
import urllib.request
import csv

symbols = ["aapl.us", "aapl", "aapl.US", "msft.us", "^spx", "spy.us"]
for s in symbols:
    url = f"https://stooq.com/q/d/l/?s={s}&i=d"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            raw = r.read().decode()
        rows = list(csv.reader(io.StringIO(raw)))
        ok = len(rows) > 1 and rows[1][0] != "No data"
        print(f"{s:10s} -> OK rows={len(rows)-1} last={rows[-1][:3] if ok else 'n/a'}")
    except Exception as e:
        print(f"{s:10s} -> FAIL {type(e).__name__}: {str(e)[:80]}")
