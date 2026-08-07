from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from fastapi import Depends, Header
from fastapi.exceptions import HTTPException

from app.config import settings
from app.providers import get_provider
from modules.ai_assistant import AIAssistantService
from modules.ai_assistant.provider import GeminiProvider
from modules.auth_billing import AuthService, UserStore
from modules.market_data.storage.parquet_store import ParquetStore
from modules.paper_trading import AccountStore, PaperTraderService
from modules.screener import ScreenerService
from modules.shared.contracts import User
from modules.strategy_engine import StrategyService, StrategyStore
from modules.trading_journal import JournalService, JournalStore


def provider_for(market: str):
    return get_provider(market)


def parquet_store() -> ParquetStore:
    return ParquetStore(Path(settings.data_dir))


_paper_store: AccountStore | None = None


def paper_service(market: str = "IN") -> PaperTraderService:
    global _paper_store
    if _paper_store is None:
        _paper_store = AccountStore(Path(settings.data_dir) / "accounts")

    def pricer(symbol: str) -> float:
        return provider_for(market).fetch_quote(symbol).price

    return PaperTraderService(_paper_store, pricer=pricer)


_strategy_service: StrategyService | None = None


def strategy_service() -> StrategyService:
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService(
            StrategyStore(Path(settings.data_dir) / "strategies")
        )
    return _strategy_service


_assistant_service: AIAssistantService | None = None


def assistant_service() -> AIAssistantService:
    global _assistant_service
    if _assistant_service is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            generator = GeminiProvider(api_key=api_key)
        else:

            class _Fallback:
                def generate(self, prompt: str) -> str:
                    return "AI assistant is not configured: set GEMINI_API_KEY to enable."

            generator = _Fallback()
        _assistant_service = AIAssistantService(generator)
    return _assistant_service


_auth_service: AuthService | None = None


def auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(UserStore(Path(settings.data_dir) / "auth"))
    return _auth_service


def current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    user = auth_service().user_for_token(authorization[len("Bearer "):])
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user


def require_plan(plan: str) -> Callable:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.plan != plan:
            raise HTTPException(
                status_code=403, detail=f"{plan} plan required"
            )
        return user

    return dependency


_journal_service: JournalService | None = None


def journal_service() -> JournalService:
    global _journal_service
    if _journal_service is None:
        _journal_service = JournalService(
            JournalStore(Path(settings.data_dir) / "journal")
        )
    return _journal_service


def screener_service(market: str) -> ScreenerService:
    provider = provider_for(market)

    def loader(symbol: str):
        from datetime import date, timedelta

        import pandas as pd

        return provider.fetch_ohlcv(
            symbol,
            "1d",
            pd.Timestamp(date.today() - timedelta(days=730)),
            pd.Timestamp(date.today()),
        )

    return ScreenerService(loader)
