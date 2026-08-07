from modules.market_data import (
    BinanceProvider,
    NSEArchiveProvider,
    ParquetStore,
    YFinanceProvider,
)
from modules.shared.contracts import MarketDataProvider

from app.config import settings


def get_provider(market: str) -> MarketDataProvider:
    store = ParquetStore(settings.data_dir)
    market = market.upper()
    if market == "IN":
        return NSEArchiveProvider(store=store)
    if market == "US":
        return YFinanceProvider(store=store)
    if market == "CRYPTO":
        return BinanceProvider(store=store)
    raise ValueError(f"unsupported market: {market}")
