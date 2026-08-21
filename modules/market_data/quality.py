from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import pandas as pd

REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")
_INTERVALS = {"1m": timedelta(minutes=1), "5m": timedelta(minutes=5),
              "15m": timedelta(minutes=15), "30m": timedelta(minutes=30),
              "1h": timedelta(hours=1), "1d": timedelta(days=1)}


@dataclass(frozen=True)
class DataQualityReport:
    ok: bool
    complete: bool
    expected_bars: int | None
    actual_bars: int
    missing_timestamps: tuple[str, ...] = ()
    duplicate_timestamps: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_ohlcv(
    df: pd.DataFrame,
    interval: str,
    expected_index: pd.DatetimeIndex | None = None,
) -> DataQualityReport:
    """Validate OHLCV without repairing or mutating the input frame.

    ``complete`` is true only when an explicit expected index is supplied and
    the normalized timestamps match it exactly. Without an expected index the
    data can be structurally valid, but completeness is deliberately unknown.
    """
    errors: list[str] = []
    warnings: list[str] = []
    missing: tuple[str, ...] = ()
    duplicates: tuple[str, ...] = ()
    if not isinstance(df, pd.DataFrame):
        return DataQualityReport(False, False, None, 0, errors=("data is not a DataFrame",))
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        errors.append(f"missing columns: {', '.join(missing_columns)}")
        return DataQualityReport(False, False, None, len(df), errors=tuple(errors))
    index = pd.DatetimeIndex(df.index)
    if not index.is_monotonic_increasing:
        errors.append("timestamps are not ordered")
    duplicate_values = index[index.duplicated(keep=False)].unique()
    duplicates = tuple(str(value) for value in duplicate_values)
    if duplicates:
        errors.append("duplicate timestamps present")
    if index.tz is None:
        warnings.append("timestamps have no timezone")
    for column in REQUIRED_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce")
        if values.isna().any():
            errors.append(f"{column} contains null or non-numeric values")
    if not errors or all("contains null" not in error for error in errors):
        numeric = df.loc[:, REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
        invalid = (
            (numeric["high"] < numeric[["open", "close"]].max(axis=1))
            | (numeric["low"] > numeric[["open", "close"]].min(axis=1))
            | (numeric["high"] < numeric["low"])
            | (numeric["volume"] < 0)
        )
        if invalid.any():
            errors.append(f"invalid OHLCV relationships in {int(invalid.sum())} bars")
    expected_count = len(expected_index) if expected_index is not None else None
    complete = False
    if expected_index is not None:
        expected = pd.DatetimeIndex(expected_index)
        actual = index
        if expected.tz is not None and actual.tz is None:
            actual = actual.tz_localize(expected.tz)
        if expected.tz is None and actual.tz is not None:
            actual = actual.tz_localize(None)
        missing = tuple(str(value) for value in expected.difference(actual))
        unexpected = tuple(str(value) for value in actual.difference(expected))
        if missing:
            errors.append("required timestamps are missing")
        if unexpected:
            errors.append("unexpected timestamps are present")
        complete = not missing and not unexpected and len(actual) == len(expected)
    else:
        warnings.append("completeness not proven: expected session index not supplied")
    if interval not in _INTERVALS:
        errors.append(f"unsupported interval: {interval}")
    return DataQualityReport(
        ok=not errors,
        complete=complete,
        expected_bars=expected_count,
        actual_bars=len(df),
        missing_timestamps=missing,
        duplicate_timestamps=duplicates,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def expected_contiguous_index(start, end, interval: str) -> pd.DatetimeIndex:
    """Build an exact expected index for already-filtered session data."""
    if interval not in _INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    return pd.date_range(start=start, end=end, freq=_INTERVALS[interval])
