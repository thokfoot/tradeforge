from datetime import date

import pandas as pd

from modules.market_data.canonical import normalize_bhavcopy, normalize_indices, slugify


def _bhavcopy_rows():
    return pd.DataFrame(
        {
            "SYMBOL": [" RELIANCE", " TCS"],
            "SERIES": [" EQ", " EQ"],
            "OPEN_PRICE": [100.0, 50.0],
            "HIGH_PRICE": [110.0, 55.0],
            "LOW_PRICE": [95.0, 48.0],
            "CLOSE_PRICE": [105.0, 52.0],
            "TTL_TRD_QNTY": [1000, 2000],
            "DELIV_QTY": [" 500", " 800"],
            "DELIV_PER": [" 50.0", " 40.0"],
        }
    )


def test_slugify():
    assert slugify("Nifty 50") == "NIFTY50"
    assert slugify("Nifty Next 50") == "NIFTYNEXT50"
    assert slugify("India VIX") == "INDIAVIX"


def test_normalize_bhavcopy_strips_and_maps():
    out = normalize_bhavcopy(_bhavcopy_rows(), date(2026, 8, 5))
    assert out.index.name == "date"
    assert list(out.index)[0] == pd.Timestamp("2026-08-05")
    row = out[out["symbol"] == "RELIANCE"].iloc[0]
    assert row["symbol"] == "RELIANCE"
    assert row["open"] == 100.0
    assert row["close"] == 105.0
    assert row["volume"] == 1000
    assert row["delivery_pct"] == 50.0
    assert set(out["symbol"]) == {"RELIANCE", "TCS"}


def test_normalize_bhavcopy_drops_missing_close():
    rows = _bhavcopy_rows()
    rows.loc[0, "CLOSE_PRICE"] = None
    out = normalize_bhavcopy(rows, date(2026, 8, 5))
    assert set(out["symbol"]) == {"TCS"}


def test_normalize_indices():
    idx = pd.DataFrame(
        {
            "Index Name": ["Nifty 50", "Nifty Bank"],
            "Index Date": ["05-08-2026", "05-08-2026"],
            "Open Index Value": ["24669.2", "52000.0"],
            "High Index Value": ["24677.6", "52100.0"],
            "Low Index Value": ["24497.95", "51800.0"],
            "Closing Index Value": [24624.65, 51900.0],
            "Volume": ["355518193", "12345"],
            "P/E": ["20.91", "9.5"],
            "P/B": ["3.02", "1.2"],
            "Div Yield": ["1.26", "0.5"],
        }
    )
    out = normalize_indices(idx, date(2026, 8, 5))
    assert set(out["symbol"]) == {"NIFTY50", "NIFTYBANK"}
    row = out[out["symbol"] == "NIFTY50"].iloc[0]
    assert row["close"] == 24624.65
    assert row["name"] == "Nifty 50"
    assert row["pe"] == 20.91
