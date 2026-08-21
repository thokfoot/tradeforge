from __future__ import annotations

import dataclasses
import hashlib
import json

import numpy as np
import pandas as pd

from modules.backtest_engine.metrics import compute_metrics
from modules.backtest_engine.simulator import simulate
from modules.market_data.quality import validate_ohlcv
from modules.shared.contracts import (
    BacktestResult,
    CostModel,
    DataBundle,
    Metrics,
    Strategy,
)
from modules.strategy_engine.sandbox import run_code


class EventDrivenEngine:
    def run(
        self,
        strategy: Strategy,
        data: DataBundle,
        costs: CostModel,
    ) -> BacktestResult:
        if data.df.empty:
            raise ValueError("data bundle has no bars")
        quality = validate_ohlcv(data.df, data.interval)
        if not quality.ok:
            raise ValueError("invalid market data: " + "; ".join(quality.errors))
        signals = self._signals(strategy, data)
        equity, trades = simulate(data, signals, costs, strategy.config)
        metrics = compute_metrics(equity, trades)
        return BacktestResult(
            strategy_id=strategy.id,
            symbol=data.symbol.symbol,
            interval=data.interval,
            start=data.df.index[0],
            end=data.df.index[-1],
            equity_curve=equity,
            trades=trades,
            metrics=metrics,
            run_hash=self.reproducible_hash(
                strategy, data.data_version, strategy.params
            ),
            data_version=data.data_version,
            execution_model="CONSERVATIVE_OHLCV_SL_FIRST",
        )

    def metrics(self, result: BacktestResult) -> Metrics:
        return result.metrics

    def reproducible_hash(
        self,
        strategy: Strategy,
        data_version: str,
        params: dict,
    ) -> str:
        payload = {
            "strategy_id": strategy.id,
            "version": strategy.version,
            "params": params,
            "data_version": data_version,
            "config": dataclasses.asdict(strategy.config),
        }
        digest = hashlib.sha256()
        digest.update(json.dumps(payload, sort_keys=True, default=str).encode())
        return digest.hexdigest()

    def _signals(self, strategy: Strategy, data: DataBundle) -> pd.Series:
        ns = run_code(
            strategy.code,
            {"np": np, "pd": pd, "data": data.df, "params": strategy.params},
            timeout=20.0,
        )
        signals = ns.get("signals")
        if not isinstance(signals, pd.Series):
            raise ValueError("strategy code must set 'signals' as a pandas Series")
        signals = signals.reindex(data.df.index).fillna(0).clip(-1, 1).astype(int)
        return signals
