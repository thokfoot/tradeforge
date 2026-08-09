from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

import pandas as pd

from modules.shared.contracts.models import (
    Account,
    AlertNotification,
    AlertRule,
    AssistantReply,
    BacktestResult,
    CostModel,
    Metrics,
    Order,
    Position,
    Quote,
    Session,
    SymbolInfo,
    Strategy,
    Trade,
    User,
    ValidationResult,
)


@runtime_checkable
class MarketDataProvider(Protocol):
    def get_symbols(self) -> list[SymbolInfo]: ...

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame: ...

    def fetch_quote(self, symbol: str) -> Quote: ...


@runtime_checkable
class StrategyService(Protocol):
    def validate(self, strategy: Strategy) -> ValidationResult: ...

    def save(self, strategy: Strategy) -> Strategy: ...

    def list_versions(self, strategy_id: str) -> list[str]: ...


@runtime_checkable
class BacktestEngine(Protocol):
    def run(
        self,
        strategy: Strategy,
        data: DataBundle,
        costs: CostModel,
    ) -> BacktestResult: ...

    def metrics(self, result: BacktestResult) -> Metrics: ...

    def reproducible_hash(
        self,
        strategy: Strategy,
        data_version: str,
        params: dict,
    ) -> str: ...


@runtime_checkable
class PaperTrader(Protocol):
    def place_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        qty: int,
        order_type: str,
        price: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
    ) -> Order: ...

    def positions(self, user_id: str) -> list[Position]: ...

    def history(self, user_id: str) -> list[Trade]: ...

    def reset_account(self, user_id: str) -> Account: ...

    def parity_score(self, user_id: str, strategy_id: str) -> float: ...


@runtime_checkable
class Analytics(Protocol):
    def metrics(self, trades: list[Trade]) -> dict: ...

    def equity_curve(self, trades: list[Trade]) -> pd.Series: ...

    def journal_entry(self, user_id: str, trade_id: str, note: str) -> None: ...


@runtime_checkable
class AIAssistant(Protocol):
    def chat(self, user_id: str, message_text_or_audio: str) -> AssistantReply: ...

    def confirm_action(self, user_id: str, proposed_action: str) -> bool: ...

    def review_journal(self, user_id: str, entries: list) -> str: ...


@runtime_checkable
class AuthService(Protocol):
    def register(self, email: str, password: str) -> User: ...

    def login(self, email: str, password: str) -> Session: ...

    def create_subscription(self, user_id: str, plan: str) -> User: ...


@runtime_checkable
class NotificationService(Protocol):
    def send(self, user_id: str, channel: str, message: str) -> None: ...


@runtime_checkable
class AlertService(Protocol):
    def create_rule(
        self,
        user_id: str,
        symbol: str,
        market: str,
        metric: str,
        condition: str,
        value: float,
    ) -> AlertRule: ...

    def list_rules(self, user_id: str) -> list[AlertRule]: ...

    def delete_rule(self, user_id: str, rule_id: str) -> bool: ...

    def notifications(self, user_id: str) -> list[AlertNotification]: ...

    def clear_notifications(self, user_id: str) -> int: ...


@runtime_checkable
class EducationService(Protocol):
    def languages(self) -> list[str]: ...

    def list_lessons(self, lang: str = "hinglish") -> list[dict]: ...

    def lesson(self, lesson_id: str, lang: str = "hinglish") -> dict | None: ...

    def mark_completed(self, user_id: str, lesson_id: str) -> list[str]: ...

    def completed(self, user_id: str) -> list[str]: ...
