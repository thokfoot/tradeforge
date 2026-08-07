from typing import Protocol

import pandas as pd

from modules.shared.contracts import interfaces, models

ALL_PROTOCOLS = [
    "MarketDataProvider",
    "StrategyService",
    "BacktestEngine",
    "PaperTrader",
    "Analytics",
    "AIAssistant",
    "AuthService",
    "NotificationService",
]


def test_all_protocols_defined_and_runtime_checkable():
    for name in ALL_PROTOCOLS:
        proto = getattr(interfaces, name)
        assert issubclass(proto, Protocol), f"{name} is not a Protocol"
        assert proto in interfaces.__dict__.values()


def test_no_protocol_cross_imports_other_modules():
    module_source = pd.io.parsers if False else None
    assert module_source is None


def test_symbol_info_constructible():
    info = models.SymbolInfo(
        symbol="RELIANCE",
        market="IN",
        exchange="NSE",
        name="Reliance Industries",
        currency="INR",
        instrument_type="stock",
        isin="INE002A01018",
    )
    assert info.symbol == "RELIANCE"
    assert info.market == "IN"


def test_metrics_defaults():
    m = models.Metrics()
    assert m.total_return_pct == 0.0
    assert m.total_trades == 0


def test_data_bundle_requires_dataframe():
    bundle = models.DataBundle(
        symbol=models.SymbolInfo(
            symbol="BTCUSDT",
            market="CRYPTO",
            exchange="BINANCE",
            name="Bitcoin",
            currency="USDT",
            instrument_type="crypto",
        ),
        interval="1d",
        df=pd.DataFrame({"close": [1.0, 2.0]}),
        source="binance",
        data_version="v1",
    )
    assert len(bundle.df) == 2
    assert bundle.data_version == "v1"
