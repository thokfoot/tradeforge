import argparse
import os
import pathlib
import sys
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from modules.market_data import NSEArchiveProvider, ParquetStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill India (NSE) EOD data to Parquet")
    parser.add_argument("--symbols", nargs="+", default=["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"])
    parser.add_argument("--all-stocks", action="store_true", help="backfill every stock in the latest NSE bhavcopy")
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--days", type=int, help="use a recent number of calendar days instead of years")
    parser.add_argument("--indices", action="store_true", help="also backfill all indices")
    parser.add_argument("--data-dir", default=os.environ.get("DATA_DIR", "data"))
    args = parser.parse_args()

    store = ParquetStore(args.data_dir)
    provider = NSEArchiveProvider(store=store)
    end = date.today()
    start = end - timedelta(days=args.days if args.days is not None else args.years * 366)

    symbols = args.symbols
    if args.all_stocks:
        latest = None
        for offset in range(7):
            try:
                latest = provider._fetch_bhavcopy(end - timedelta(days=offset))
                break
            except Exception:
                continue
        if latest is None:
            raise RuntimeError("could not find a recent NSE trading day for the stock universe")
        symbols = sorted(latest["symbol"].dropna().unique().tolist())
        print(f"stocks: {len(symbols)} from latest NSE bhavcopy")

    stats = provider.backfill(symbols, interval="1d", start=start, end=end)
    for symbol, days in stats.items():
        print(f"{symbol}: {days} days")
    if args.indices:
        n = provider.backfill_indices(start, end)
        print(f"indices: {n} days")
    print(f"store: {store.root.resolve()}")


if __name__ == "__main__":
    main()
