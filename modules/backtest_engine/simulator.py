from __future__ import annotations

import pandas as pd

from modules.shared.contracts import CostModel, DataBundle, Side, StrategyConfig, Trade


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
        size = int((cash * cfg.position_size / 100.0) // fill)
        if size > 0:
            return size
        return 1 if cash >= fill else 0
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
    entry_time = None
    sl_price: float | None = None
    tp_price: float | None = None
    sl_pct = cfg.stop_loss_pct
    tp_pct = cfg.take_profit_pct
    allow_short = bool(getattr(cfg, "allow_short", False))
    trades: list[Trade] = []
    equity: list[float] = []

    def open_position(t: int, fill: float, side: Side) -> None:
        nonlocal cash, qty, entry_price, entry_fees, entry_time, sl_price, tp_price
        size = _sizing(cfg, cash, fill)
        if size <= 0:
            return
        notional = size * fill
        fees = order_charges(costs, notional, side)
        if side == "BUY":
            cash -= notional + fees
            qty = size
            sl_price = fill * (1.0 - sl_pct / 100.0) if sl_pct else None
            tp_price = fill * (1.0 + tp_pct / 100.0) if tp_pct else None
        else:
            cash += notional - fees
            qty = -size
            sl_price = fill * (1.0 + sl_pct / 100.0) if sl_pct else None
            tp_price = fill * (1.0 - tp_pct / 100.0) if tp_pct else None
        entry_price = fill
        entry_fees = fees
        entry_time = df.index[t]
        trades.append(
            Trade(
                order_id=f"T{len(trades) + 1}",
                symbol=data.symbol.symbol,
                side=side,
                qty=size,
                price=fill,
                fees=fees,
                pnl=0.0,
                timestamp=df.index[t],
                entry_timestamp=None,
            )
        )

    def close_position(t: int, fill: float, side: Side) -> None:
        nonlocal cash, qty, entry_price, entry_fees, entry_time, sl_price, tp_price
        units = abs(qty)
        notional = units * fill
        fees = order_charges(costs, notional, side)
        if qty > 0:
            pnl = (fill - entry_price) * units - entry_fees - fees
            cash += notional - fees
        else:
            pnl = (entry_price - fill) * units - entry_fees - fees
            cash -= notional + fees
        trades.append(
            Trade(
                order_id=f"T{len(trades) + 1}",
                symbol=data.symbol.symbol,
                side=side,
                qty=units,
                price=fill,
                fees=entry_fees + fees,
                pnl=pnl,
                timestamp=df.index[t],
                entry_timestamp=entry_time,
            )
        )
        qty = 0
        entry_price = 0.0
        entry_fees = 0.0
        entry_time = None
        sl_price = None
        tp_price = None

    for t in range(len(df)):
        close = float(df["close"].iloc[t])
        if t > 0:
            target = int(signals.iloc[t - 1])
            open_px = float(df["open"].iloc[t])
            if target == 1:
                if qty == 0:
                    open_position(t, open_px * (1.0 + costs.slippage_pct), "BUY")
                elif qty < 0:
                    close_position(t, open_px * (1.0 + costs.slippage_pct), "BUY")
            elif target == -1:
                if qty > 0:
                    close_position(t, open_px * (1.0 - costs.slippage_pct), "SELL")
                elif qty == 0 and allow_short:
                    open_position(t, open_px * (1.0 - costs.slippage_pct), "SELL")
        if qty != 0 and (sl_price is not None or tp_price is not None):
            low = float(df["low"].iloc[t])
            high = float(df["high"].iloc[t])
            if qty > 0:
                if sl_price is not None and low <= sl_price:
                    close_position(t, sl_price * (1.0 - costs.slippage_pct), "SELL")
                elif tp_price is not None and high >= tp_price:
                    close_position(t, tp_price * (1.0 - costs.slippage_pct), "SELL")
            else:
                if sl_price is not None and high >= sl_price:
                    close_position(t, sl_price * (1.0 + costs.slippage_pct), "BUY")
                elif tp_price is not None and low <= tp_price:
                    close_position(t, tp_price * (1.0 + costs.slippage_pct), "BUY")
        equity.append(cash + qty * close)
    if qty > 0:
        t = len(df) - 1
        fill = float(df["close"].iloc[t]) * (1.0 - costs.slippage_pct)
        close_position(t, fill, "SELL")
        equity[-1] = cash
    elif qty < 0:
        t = len(df) - 1
        fill = float(df["close"].iloc[t]) * (1.0 + costs.slippage_pct)
        close_position(t, fill, "BUY")
        equity[-1] = cash
    return pd.Series(equity, index=df.index, name="equity"), trades
