import numpy as np
import pandas as pd

from modules.screener import ScreenerService
from modules.shared.contracts import ScreenerRow


def make_series(n: int = 250, start: float = 100.0, growth: float = 0.0):
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    rng = np.random.default_rng(7)
    noise = np.cumsum(rng.normal(0, 0.3, n))
    trend = start * (1 + growth) ** np.arange(n)
    close = pd.Series(trend + noise, index=idx)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 10_000.0),
        },
        index=idx,
    )


def loader(symbol: str) -> pd.DataFrame:
    if symbol == "RISER":
        return make_series(growth=0.002)
    if symbol == "FALLER":
        return make_series(growth=-0.002)
    if symbol == "SHORT":
        return make_series(n=1)
    return make_series()


def test_scan_returns_rows():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER", "FLAT", "SHORT"])
    assert all(isinstance(r, ScreenerRow) for r in rows)
    assert len(rows) == 3


def test_price_filter():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER"], {"min_price": 150})
    assert [r.symbol for r in rows] == ["RISER"]


def test_sort_by_change_desc():
    service = ScreenerService(loader)
    rows = service.scan(["FALLER", "RISER"], {"sort_by": "change_1m_pct"})
    assert rows[0].symbol == "RISER"
    assert rows[1].symbol == "FALLER"


def test_bool_filter_above_sma():
    service = ScreenerService(loader)
    rows = service.scan(["RISER", "FALLER"], {"above_sma_200": True})
    assert [r.symbol for r in rows] == ["RISER"]


def test_single_bar_series_skipped():
    service = ScreenerService(loader)
    rows = service.scan(["SHORT"], {})
    assert rows == []


def test_bad_symbol_skipped():
    service = ScreenerService(lambda s: (_ for _ in ()).throw(ValueError("boom")))
    assert service.scan(["X"]) == []


def test_short_series_metrics_none():
    service = ScreenerService(loader)
    row = service._metrics("PARTIAL", make_series(n=30))
    assert row.change_3m_pct is None
    assert row.above_sma_200 is None
    assert row.change_1d_pct is not None
