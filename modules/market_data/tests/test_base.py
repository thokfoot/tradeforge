import pandas as pd
import pytest

from modules.market_data.providers.base import ParquetBackedProvider
from modules.market_data.storage.parquet_store import ParquetStore

from datetime import date


class FakeProvider(ParquetBackedProvider):
    market = "TEST"
    currency = "X"
    supported_intervals = {"1d"}

    def __init__(self, store=None):
        super().__init__(store=store)
        self.calls = []

    def _fetch_range(self, symbol, interval, start, end):
        self.calls.append((start.date(), end.date()))
        idx = pd.date_range(start, end, freq="B")
        return pd.DataFrame(
            {"close": [1.0] * len(idx), "volume": [10] * len(idx)}, index=idx
        )


@pytest.fixture
def provider(tmp_path) -> FakeProvider:
    return FakeProvider(store=ParquetStore(tmp_path))


def test_fetch_ohlcv_fetches_and_persists(provider):
    df = provider.fetch_ohlcv(
        "X", "1d", pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-07")
    )
    assert len(df) == 5
    assert provider.calls == [(date(2026, 8, 3), date(2026, 8, 7))]


def test_fetch_ohlcv_second_call_uses_store(provider):
    start, end = pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-07")
    provider.fetch_ohlcv("X", "1d", start, end)
    first_calls = list(provider.calls)
    provider.fetch_ohlcv("X", "1d", start, end)
    assert provider.calls == first_calls


def test_uncovered_ranges_middle_gap():
    covered = {date(2026, 8, 5)}
    ranges = ParquetBackedProvider._uncovered_ranges(
        date(2026, 8, 3), date(2026, 8, 7), covered
    )
    assert ranges == [
        (date(2026, 8, 3), date(2026, 8, 4)),
        (date(2026, 8, 6), date(2026, 8, 7)),
    ]


def test_fetch_ohlcv_fetches_only_gaps(provider):
    provider.store.write(
        "TEST", "1d", "X",
        pd.DataFrame(
            {"close": [5.0]},
            index=pd.DatetimeIndex(["2026-08-05"], name="date"),
        ),
    )
    df = provider.fetch_ohlcv(
        "X", "1d", pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-07")
    )
    assert len(df) == 5
    assert set(provider.calls) == {
        (date(2026, 8, 3), date(2026, 8, 4)),
        (date(2026, 8, 6), date(2026, 8, 7)),
    }


def test_fetch_ohlcv_rejects_unsupported_interval(provider):
    with pytest.raises(ValueError):
        provider.fetch_ohlcv(
            "X", "1h", pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-07")
        )


def test_backfill_returns_row_counts(provider):
    stats = provider.backfill(
        ["X"], "1d", pd.Timestamp("2026-08-03"), pd.Timestamp("2026-08-04")
    )
    assert stats == {"X": 2}
