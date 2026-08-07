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
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--indices", action="store_true", help="also backfill all indices")
    parser.add_argument("--data-dir", default=os.environ.get("DATA_DIR", "data"))
    args = parser.parse_args()

    store = ParquetStore(args.data_dir)
    provider = NSEArchiveProvider(store=store)
    end = date.today()
    start = end - timedelta(days=args.years * 366)

    stats = provider.backfill(args.symbols, start, end)
    for symbol, days in stats.items():
        print(f"{symbol}: {days} days")
    if args.indices:
        n = provider.backfill_indices(start, end)
        print(f"indices: {n} days")
    print(f"store: {store.root.resolve()}")


if __name__ == "__main__":
    main()
