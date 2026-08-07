from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd

from modules.alerts.store import AlertStore
from modules.shared.contracts import AlertNotification, AlertRule

ProviderGetter = Callable[[str], object]

VALID_METRICS = {"PRICE", "RSI"}
VALID_CONDITIONS = {"ABOVE", "BELOW"}


class AlertService:
    def __init__(self, store: AlertStore):
        self._store = store

    def create_rule(
        self,
        user_id: str,
        symbol: str,
        market: str,
        metric: str,
        condition: str,
        value: float,
    ) -> AlertRule:
        metric = metric.upper()
        condition = condition.upper()
        if metric not in VALID_METRICS:
            raise ValueError(f"unsupported metric: {metric}")
        if condition not in VALID_CONDITIONS:
            raise ValueError(f"unsupported condition: {condition}")
        if value <= 0:
            raise ValueError("alert value must be positive")
        rule = AlertRule(
            rule_id=uuid.uuid4().hex[:12],
            user_id=user_id,
            symbol=symbol,
            market=market,
            metric=metric,
            condition=condition,
            value=float(value),
            active=True,
            created_at=datetime.utcnow(),
        )
        rules = self._store.rules(user_id)
        rules.append(asdict(rule))
        self._store.save_rules(user_id, rules)
        return rule

    def list_rules(self, user_id: str) -> list[AlertRule]:
        return [AlertRule(**r) for r in self._store.rules(user_id)]

    def delete_rule(self, user_id: str, rule_id: str) -> bool:
        rules = self._store.rules(user_id)
        remaining = [r for r in rules if r["rule_id"] != rule_id]
        if len(remaining) == len(rules):
            return False
        self._store.save_rules(user_id, remaining)
        return True

    def notifications(self, user_id: str) -> list[AlertNotification]:
        return [AlertNotification(**n) for n in self._store.notifications(user_id)]

    def clear_notifications(self, user_id: str) -> int:
        return self._store.clear_notifications(user_id)

    def check_user(
        self, user_id: str, provider_for: ProviderGetter
    ) -> list[AlertNotification]:
        triggered: list[AlertNotification] = []
        for rule in self.list_rules(user_id):
            if not rule.active:
                continue
            try:
                hit, current = self._evaluate(rule, provider_for)
            except Exception:
                continue
            if not hit:
                continue
            self._deactivate(user_id, rule.rule_id)
            notif = AlertNotification(
                id=uuid.uuid4().hex[:12],
                user_id=user_id,
                rule_id=rule.rule_id,
                symbol=rule.symbol,
                message=self._message(rule, current),
                created_at=datetime.utcnow(),
            )
            self._store.add_notification(user_id, asdict(notif))
            triggered.append(notif)
        return triggered

    def check_all(self, provider_for: ProviderGetter) -> list[AlertNotification]:
        triggered: list[AlertNotification] = []
        for user_id in self._store.user_ids():
            triggered.extend(self.check_user(user_id, provider_for))
        return triggered

    def _evaluate(self, rule: AlertRule, provider_for: ProviderGetter) -> tuple[bool, float | None]:
        provider = provider_for(rule.market)
        if rule.metric == "PRICE":
            current = float(provider.fetch_quote(rule.symbol).price)
        else:
            df = provider.fetch_ohlcv(
                rule.symbol,
                "1d",
                pd.Timestamp(datetime.utcnow() - timedelta(days=120)),
                pd.Timestamp(datetime.utcnow()),
            )
            if df is None or df.empty:
                return False, None
            current = _rsi(df["close"], 14)
        if current is None:
            return False, None
        if rule.condition == "ABOVE":
            return current >= rule.value, current
        return current <= rule.value, current

    def _deactivate(self, user_id: str, rule_id: str) -> None:
        rules = [asdict(r) for r in self.list_rules(user_id)]
        for rule in rules:
            if rule["rule_id"] == rule_id:
                rule["active"] = False
        self._store.save_rules(user_id, rules)

    @staticmethod
    def _message(rule: AlertRule, current: float) -> str:
        direction = "upar" if rule.condition == "ABOVE" else "neeche"
        return (
            f"{rule.symbol} {rule.metric} {direction} target {rule.value} "
            f"touch ho gaya (abhi {round(current, 2)})."
        )


def _rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) <= period:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return float(100.0 - 100.0 / (1.0 + rs))
