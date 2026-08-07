import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd

from modules.backtest_engine import EventDrivenEngine
from modules.market_data import NSEArchiveProvider, ParquetStore
from modules.shared.contracts import (
    CostModel,
    DataBundle,
    Strategy,
    StrategyConfig,
    SymbolInfo,
)

store = ParquetStore(r"C:\Users\Mind\AppData\Local\Temp\opencode\tf_smoke")
provider = NSEArchiveProvider(store=store)
df = provider.fetch_ohlcv(
    "RELIANCE", "1d", pd.Timestamp("2026-07-27"), pd.Timestamp("2026-08-07")
)
print(f"bars: {len(df)} | {df.index[0].date()} -> {df.index[-1].date()}")

symbol = SymbolInfo(
    symbol="RELIANCE",
    market="IN",
    exchange="NSE",
    name="Reliance Industries",
    currency="INR",
    instrument_type="stock",
)
bundle = DataBundle(
    symbol=symbol,
    interval="1d",
    df=df,
    source="nse-archives",
    data_version="v1",
)

code = 'signals = pd.Series(np.where(data["close"] > data["close"].rolling(20).mean(), 1, 0), index=data.index)'
strategy = Strategy(
    id="sma20",
    version="1.0",
    author_user_id="u1",
    code=code,
    config=StrategyConfig(
        initial_capital=100000.0, position_sizing="pct", position_size=100.0
    ),
)

costs = CostModel(
    brokerage=20.0,
    stt_pct=0.001,
    exchange_charges_pct=0.0000345,
    sebi_fees_pct=0.000001,
    gst_pct=0.18,
    stamp_duty_pct=0.00015,
    slippage_pct=0.0005,
)
result = EventDrivenEngine().run(strategy, bundle, costs)
m = result.metrics
print(
    f"trades={m.total_trades} ret={m.total_return_pct:.2f}% "
    f"cagr={m.cagr_pct:.2f}% sharpe={m.sharpe:.2f} "
    f"maxDD={m.max_drawdown_pct:.2f}% winrate={m.win_rate_pct:.1f}% "
    f"PF={m.profit_factor:.2f}"
)
print("run_hash:", result.run_hash[:16])
