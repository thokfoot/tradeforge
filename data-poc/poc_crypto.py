"""Data PoC — Crypto (Binance public API). Throwaway verification script."""
import json
import urllib.request
import urllib.parse

BASE = "https://api.binance.com/api/v3/klines"


def klines(symbol, interval, limit=1000, start_time=None):
    q = {"symbol": symbol, "interval": interval, "limit": str(limit)}
    if start_time:
        q["startTime"] = str(start_time)
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


# 1) Daily — one call (1000 bars ~ 2.7y) + pagination for depth
d1 = klines("BTCUSDT", "1d", 1000)
print(f"BTCUSDT 1d: rows={len(d1)}  {d1[0][0]} -> {d1[-1][0]}")
print("bar sample:", d1[-1][:9])

# paginate back 5 years using startTime of first bar
first_ts = d1[0][0]
older = klines("BTCUSDT", "1d", 1000, start_time=first_ts - 1000 * 86400 * 1000)
print(f"older block: rows={len(older)}  {older[0][0]} -> {older[-1][0]}")


def ts(s):
    import datetime as dt
    return dt.datetime.utcfromtimestamp(int(s) / 1000).strftime("%Y-%m-%d %H:%M")


# 2) Intraday 1m — depth test (1 call limit 1000, paginate by startTime)
m1 = klines("BTCUSDT", "1m", 1000)
print(f"\nBTCUSDT 1m: rows={len(m1)}  {ts(m1[0][0])} -> {ts(m1[-1][0])}")

# 3) data.binance.vision monthly archive (deep history) — just check availability
import urllib.request as u
url = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip"
try:
    req = u.Request(url, method="HEAD")
    with u.urlopen(req, timeout=20) as r:
        print(f"\nbinance.vision monthly archive 2020-01: HTTP {r.status}, size={r.headers.get('Content-Length')}")
except Exception as e:
    print("\narchive check failed:", str(e)[:120])
