"""Export the Parquet data store to CSV files in a target folder, then commit
them into a local git repository. This is the "export my data to my own git"
feature (owner's data-ownership vision) as an offline CLI.

Usage:
    python scripts/export_to_git.py --data data --repo C:/my-data-backup
    python scripts/export_to_git.py --data data --repo C:/my-data-backup --dry-run
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from modules.market_data.storage.parquet_store import ParquetStore  # noqa: E402


def collect_files(store: ParquetStore) -> list[tuple[str, Path]]:
    files = []
    for market_dir in store.root.iterdir():
        if not market_dir.is_dir():
            continue
        for interval_dir in market_dir.iterdir():
            if not interval_dir.is_dir():
                continue
            for parquet in interval_dir.glob("*.parquet"):
                csv_rel = Path(market_dir.name) / interval_dir.name / f"{parquet.stem}.csv"
                files.append((str(csv_rel), parquet))
    return files


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Parquet store to CSV in a git repo")
    parser.add_argument("--data", default="data", help="Parquet store root (DATA_DIR)")
    parser.add_argument("--repo", default="data-backup", help="target folder (git repo)")
    parser.add_argument("--dry-run", action="store_true", help="print plan without writing")
    parser.add_argument("--message", default="data export", help="git commit message")
    args = parser.parse_args()

    store = ParquetStore(Path(args.data))
    files = collect_files(store)
    if not files:
        print("no parquet files found under", args.data)
        return 1

    repo = Path(args.repo)
    print(f"{len(files)} parquet files -> CSV in {repo}")

    if args.dry_run:
        for rel, _ in files:
            print("  would write", rel)
        return 0

    repo.mkdir(parents=True, exist_ok=True)
    for rel, parquet in files:
        out = repo / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        df = pd.read_parquet(parquet)
        df.to_csv(out)
        print("  wrote", rel)

    if not (repo / ".git").exists():
        run(["git", "init"], repo)
    run(["git", "add", "-A"], repo)
    run(["git", "commit", "-m", args.message], repo)
    print("committed to", repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
