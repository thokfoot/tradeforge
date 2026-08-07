from __future__ import annotations

import pandas as pd

from modules.shared.contracts import CostModel, DataBundle, StrategyConfig, Trade


def order_charges(c: CostModel, notional: float, side: str) -> float:
    brokerage = max(c.brokerage, notional * c.brokerage_pct)
    stt = notional * c.stt_pct if side == "SELL" else 0.0
    exchange = notional * c.exchange_charges_pct
    sebi = notional * c.sebi_fees_pct
    gst = (brokerage + exchange) * c.gst_pct
    stamp = notional * c.stamp_duty_pct if side == "BUY" else 0.0
    return brokerage + stt + exchange + sebi + gst + stamp


def _sizing(cfg: StrategyConfig, cash: float, fill: float) -> int:
    if cfg.position_sizing == "fixed":
        return int(cfg.position_size)
    if cfg.position_sizing == "pct":
        return int((cash * cfg.position_size / 100.0) // fill)
    return 0


def simulate(
    data: DataBundle,
    signals: pd.Series,
    costs: CostModel,
    cfg: StrategyConfig,
) -> tuple[pd.Series, list[Trade]]:
    df = data.df
    signals = signals.reindex(df.index).fillna(0).astype(int)
    cash = float(cfg.initial_capital)
    qty = 0
    entry_price = 0.0
    entry_fees = 0.0
    trades: list[Trade] = []
    equity: list[float] = []
    for t in range(len(df)):
        close = float(df["close"].iloc[t])
        if t > 0:
            target = int(signals.iloc[t - 1])
            open_px = float(df["open"].iloc[t])
            if target == 1 and qty == 0:
                fill = open_px * (1.0 + costs.slippage_pct)
                size = _sizing(cfg, cash, fill)
                if size > 0:
                    notional = size * fill
                    fees = order_charges(costs, notional, "BUY")
                    cash -= notional + fees
                    qty = size
                    entry_price = fill
                    entry_fees = fees
            elif target == 0 and qty > 0:
                fill = open_px * (1.0 - costs.slippage_pct)
                notional = qty * fill
                fees = order_charges(costs, notional, "SELL")
                pnl = (fill - entry_price) * qty - entry_fees - fees
                cash += notional - fees
                trades.append(
                    Trade(
                        order_id=f"T{len(trades) + 1}",
                        symbol=data.symbol.symbol,
                        side="SELL",
                        qty=qty,
                        price=fill,
                        fees=entry_fees + fees,
                        pnl=pnl,
                        timestamp=df.index[t],
                    )
                )
                qty = 0
                entry_price = 0.0
                entry_fees = 0.0
        equity.append(cash + qty * close)
    return pd.Series(equity, index=df.index, name="equity"), trades
