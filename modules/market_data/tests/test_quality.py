import pandas as pd

from modules.market_data.quality import expected_contiguous_index, validate_ohlcv


def frame(index):
    return pd.DataFrame(
        {"open": [10.0] * len(index), "high": [11.0] * len(index),
         "low": [9.0] * len(index), "close": [10.0] * len(index),
         "volume": [100.0] * len(index)}, index=index
    )


def test_quality_requires_explicit_completeness_index():
    index = pd.date_range("2026-01-01", periods=3, freq="min")
    report = validate_ohlcv(frame(index), "1m")
    assert report.ok
    assert not report.complete
    assert report.expected_bars is None


def test_quality_rejects_missing_timestamp():
    expected = pd.date_range("2026-01-01", periods=3, freq="min")
    actual = expected.delete(1)
    report = validate_ohlcv(frame(actual), "1m", expected)
    assert not report.ok
    assert not report.complete
    assert len(report.missing_timestamps) == 1


def test_quality_rejects_duplicate_timestamp():
    expected = pd.date_range("2026-01-01", periods=3, freq="min")
    actual = expected.insert(2, expected[1])
    report = validate_ohlcv(frame(actual), "1m", expected)
    assert not report.ok
    assert report.duplicate_timestamps


def test_quality_rejects_bad_ohlc_relationship():
    index = pd.date_range("2026-01-01", periods=1, freq="min")
    data = frame(index)
    data.loc[index[0], "low"] = 12.0
    report = validate_ohlcv(data, "1m")
    assert not report.ok


def test_expected_contiguous_index():
    index = expected_contiguous_index("2026-01-01 09:15", "2026-01-01 09:17", "1m")
    assert len(index) == 3
