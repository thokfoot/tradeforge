"""Data PoC — US (Stooq EOD). Throwaway verification script."""
import io
import urllib.request
import csv

URL = "https://stooq.com/q/d/l/?s=aapl.us&i=d"
try:
    with urllib.request.urlopen(URL, timeout=30) as r:
        raw = r.read().decode()
    print("stooq AAPL OK, bytes:", len(raw))
    rows = list(csv.reader(io.StringIO(raw)))
    print("header:", rows[0])
    print("rows:", len(rows) - 1)
    print("first:", rows[1])
    print("last:", rows[-1])
except Exception as e:
    print("STOOQ FAILED:", type(e).__name__, str(e)[:200])
