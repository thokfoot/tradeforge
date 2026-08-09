from __future__ import annotations

import numpy as np
import pandas as pd

from modules.shared.contracts import Metrics, Trade

TRADING_DAYS = 252


def compute_metrics(equity: pd.Series, trades: list[Trade]) -> Metrics:
    if equity.empty:
        return Metrics()
    rets = equity.pct_change().dropna()
    start, end = equity.iloc[0], equity.iloc[-1]
    total_return_pct = (end / start - 1.0) * 100.0 if start else 0.0
    years = len(equity) / TRADING_DAYS
    cagr_pct = ((end / start) ** (1.0 / years) - 1.0) * 100.0 if years > 0 and start else 0.0
    sharpe = _annualized_sharpe(rets)
    sortino = _annualized_sortino(rets)
    max_dd_pct = float((equity / equity.cummax() - 1.0).min() * 100.0)
    closed = [t for t in trades if t.entry_timestamp is not None]
    wins = [t for t in closed if t.pnl > 0]
    losses = [t for t in closed if t.pnl < 0]
    win_rate_pct = len(wins) / len(closed) * 100.0 if closed else 0.0
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float("inf") if gross_profit > 0 else 0.0
    calmar = cagr_pct / abs(max_dd_pct) if max_dd_pct < 0 else 0.0
    avg_trade_return_pct = (
        np.mean([t.pnl for t in closed]) / start * 100.0 if closed else 0.0
    )
    durations = []
    for t in trades:
        if t.entry_timestamp is not None:
            durations.append(
                (pd.Timestamp(t.timestamp) - pd.Timestamp(t.entry_timestamp))
                .total_seconds()
                / 86400.0
            )
    avg_trade_duration_days = float(np.mean(durations)) if durations else 0.0
    return Metrics(
        total_return_pct=float(total_return_pct),
        cagr_pct=float(cagr_pct),
        sharpe=float(sharpe),
        sortino=float(sortino),
        max_drawdown_pct=float(max_dd_pct),
        win_rate_pct=float(win_rate_pct),
        profit_factor=float(profit_factor),
        total_trades=len(trades),
        avg_trade_return_pct=float(avg_trade_return_pct),
        avg_trade_duration_days=float(avg_trade_duration_days),
        calmar=float(calmar),
    )


def _annualized_sharpe(rets: pd.Series) -> float:
    if rets.empty:
        return 0.0
    std = rets.std()
    if std == 0:
        return 0.0
    return float(rets.mean() / std * np.sqrt(TRADING_DAYS))


def _annualized_sortino(rets: pd.Series) -> float:
    if rets.empty:
        return 0.0
    downside = rets[rets < 0]
    std = downside.std()
    if std == 0 or std != std:
        return _annualized_sharpe(rets)
    return float(rets.mean() / std * np.sqrt(TRADING_DAYS))
