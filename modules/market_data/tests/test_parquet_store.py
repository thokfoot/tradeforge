from pathlib import Path

import pandas as pd
import pytest

from modules.market_data.storage.parquet_store import ParquetStore


@pytest.fixture
def store(tmp_path: Path) -> ParquetStore:
    return ParquetStore(tmp_path)


def _frame(dates, closes):
    idx = pd.DatetimeIndex(dates, name="date")
    return pd.DataFrame({"close": closes, "volume": [10] * len(dates)}, index=idx)


def test_write_read_roundtrip(store):
    store.write("IN", "1d", "RELIANCE", _frame(["2026-08-04", "2026-08-05"], [105.0, 106.0]))
    out = store.read("IN", "1d", "RELIANCE")
    assert out is not None
    assert list(out["close"]) == [105.0, 106.0]
    assert isinstance(out.index, pd.DatetimeIndex)


def test_has_and_missing(store):
    assert not store.has("IN", "1d", "TCS")
    store.write("IN", "1d", "TCS", _frame(["2026-08-05"], [52.0]))
    assert store.has("IN", "1d", "TCS")


def test_write_dedupes_on_overlap(store):
    store.write("IN", "1d", "RELIANCE", _frame(["2026-08-04", "2026-08-05"], [105.0, 106.0]))
    store.write("IN", "1d", "RELIANCE", _frame(["2026-08-05", "2026-08-06"], [107.0, 108.0]))
    out = store.read("IN", "1d", "RELIANCE")
    assert len(out) == 3
    assert list(out["close"]) == [105.0, 107.0, 108.0]


def test_write_empty_is_noop(store):
    store.write("IN", "1d", "RELIANCE", pd.DataFrame())
    assert not store.has("IN", "1d", "RELIANCE")
