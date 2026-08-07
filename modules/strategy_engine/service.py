from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd

from modules.shared.contracts import Strategy, ValidationResult
from modules.strategy_engine.sandbox import run_code
from modules.strategy_engine.store import StrategyStore


def _probe_data() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    close = pd.Series(
        np.sin(np.linspace(0, 6, 60)) * 5 + 100.0, index=idx
    )
    return pd.DataFrame(
        {
            "open": close + 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


class StrategyService:
    def __init__(self, store: StrategyStore, timeout: float = 2.0):
        self._store = store
        self._timeout = timeout

    def validate(self, strategy: Strategy) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        data = _probe_data()
        try:
            ns = run_code(
                strategy.code,
                {"np": np, "pd": pd, "data": data, "params": strategy.params},
                self._timeout,
            )
        except Exception as exc:
            return ValidationResult(ok=False, errors=[str(exc)], warnings=[])

        signals = ns.get("signals")
        if not isinstance(signals, pd.Series):
            return ValidationResult(
                ok=False,
                errors=["strategy code must set 'signals' as a pandas Series"],
                warnings=[],
            )
        if not signals.index.equals(data.index):
            warnings.append("signals index differs from data index; it will be reindexed")
        values = set(pd.Series(signals).dropna().astype(int).unique())
        if not values.issubset({-1, 0, 1}):
            warnings.append("signals should use values in {-1, 0, 1}")
        return ValidationResult(ok=True, errors=errors, warnings=warnings)

    def save(self, strategy: Strategy) -> Strategy:
        result = self.validate(strategy)
        if not result.ok:
            raise ValueError("; ".join(result.errors))
        version = strategy.version or f"v{len(self._store.load(strategy.id)) + 1}"
        saved = Strategy(
            id=strategy.id,
            version=version,
            author_user_id=strategy.author_user_id,
            code=strategy.code,
            params=strategy.params,
            config=strategy.config,
            data_version=strategy.data_version,
        )
        self._store.append(strategy.id, asdict(saved))
        return saved

    def list_versions(self, strategy_id: str) -> list[str]:
        return [v["version"] for v in self._store.load(strategy_id)]
