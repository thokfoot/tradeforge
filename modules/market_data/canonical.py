from __future__ import annotations

import pandas as pd

CANONICAL_COLUMNS = ["open", "high", "low", "close", "volume"]


def slugify(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch.isalnum())


def normalize_bhavcopy(df: pd.DataFrame, reporting_date) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "symbol": df["SYMBOL"].str.strip(),
            "open": pd.to_numeric(df["OPEN_PRICE"], errors="coerce"),
            "high": pd.to_numeric(df["HIGH_PRICE"], errors="coerce"),
            "low": pd.to_numeric(df["LOW_PRICE"], errors="coerce"),
            "close": pd.to_numeric(df["CLOSE_PRICE"], errors="coerce"),
            "volume": pd.to_numeric(df["TTL_TRD_QNTY"], errors="coerce"),
            "delivery_qty": pd.to_numeric(
                df["DELIV_QTY"].astype(str).str.strip(), errors="coerce"
            ),
            "delivery_pct": pd.to_numeric(
                df["DELIV_PER"].astype(str).str.strip(), errors="coerce"
            ),
        }
    )
    out["date"] = pd.to_datetime(reporting_date)
    return _finalize(out)


def normalize_indices(df: pd.DataFrame, reporting_date) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "symbol": df["Index Name"].map(slugify),
            "name": df["Index Name"],
            "open": pd.to_numeric(df["Open Index Value"], errors="coerce"),
            "high": pd.to_numeric(df["High Index Value"], errors="coerce"),
            "low": pd.to_numeric(df["Low Index Value"], errors="coerce"),
            "close": pd.to_numeric(df["Closing Index Value"], errors="coerce"),
            "volume": pd.to_numeric(df["Volume"], errors="coerce"),
            "pe": pd.to_numeric(df["P/E"], errors="coerce"),
            "pb": pd.to_numeric(df["P/B"], errors="coerce"),
            "div_yield": pd.to_numeric(df["Div Yield"], errors="coerce"),
        }
    )
    out["date"] = pd.to_datetime(reporting_date)
    return _finalize(out)


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["close"]).set_index("date")
    df.index = pd.DatetimeIndex(df.index).tz_localize(None)
    df.index.name = "date"
    return df
