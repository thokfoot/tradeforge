from __future__ import annotations

from pathlib import Path
from typing import Callable

from fastapi import Depends, Header
from fastapi.exceptions import HTTPException

from app.config import settings
from app.providers import get_provider
from modules.ai_agent import AgentBacktestStore, AgentService
from modules.ai_agent.cache import TtlCache
from modules.ai_agent.providers import CloudflareParser, GeminiProvider, GroqProvider
from modules.ai_assistant import AIAssistantService
from modules.ai_assistant.provider import GeminiProvider as AssistantGeminiProvider
from modules.alerts import AlertService, AlertStore
from modules.auth_billing import AuthService, UserStore
from modules.market_data.storage.parquet_store import ParquetStore
from modules.paper_trading import AccountStore, PaperTraderService
from modules.paper_trading.service import DEFAULT_CAPITAL
from modules.screener import ScanStore, ScreenerService
from modules.shared.contracts import User
from modules.shared.database import use_postgres
from modules.shared.pg_stores import (
    PgAccountStore,
    PgAlertStore,
    PgJournalStore,
    PgScanStore,
    PgStrategyStore,
    PgUserStore,
)
from modules.strategy_engine import StrategyService, StrategyStore
from modules.trading_journal import JournalService, JournalStore
from modules.watchlists import WatchlistStore


def provider_for(market: str):
    return get_provider(market)


def parquet_store() -> ParquetStore:
    return ParquetStore(Path(settings.data_dir))


_paper_store: AccountStore | PgAccountStore | None = None


def paper_store() -> AccountStore | PgAccountStore:
    global _paper_store
    if _paper_store is None:
        if use_postgres():
            _paper_store = PgAccountStore()
        else:
            _paper_store = AccountStore(Path(settings.data_dir) / "accounts")
    return _paper_store


def paper_service(market: str = "IN") -> PaperTraderService:
    def pricer(symbol: str) -> float:
        return provider_for(market).fetch_quote(symbol).price

    return PaperTraderService(paper_store(), pricer=pricer)


_strategy_service: StrategyService | None = None


def strategy_service() -> StrategyService:
    global _strategy_service
    if _strategy_service is None:
        store = PgStrategyStore() if use_postgres() else StrategyStore(Path(settings.data_dir) / "strategies")
        _strategy_service = StrategyService(store)
    return _strategy_service


_assistant_service: AIAssistantService | None = None


def assistant_service() -> AIAssistantService:
    global _assistant_service
    if _assistant_service is None:
        api_key = settings.gemini_api_key
        if api_key:
            generator = AssistantGeminiProvider(api_key=api_key, model=settings.gemini_model)
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
        store = PgUserStore() if use_postgres() else UserStore(Path(settings.data_dir) / "auth")
        _auth_service = AuthService(store)
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
        store = PgJournalStore() if use_postgres() else JournalStore(Path(settings.data_dir) / "journal")
        _journal_service = JournalService(store)
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


_scan_store: ScanStore | None = None


def scan_store() -> ScanStore:
    global _scan_store
    if _scan_store is None:
        _scan_store = PgScanStore() if use_postgres() else ScanStore(Path(settings.data_dir) / "screener")
    return _scan_store


_alert_service: AlertService | None = None


def alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        store = PgAlertStore() if use_postgres() else AlertStore(Path(settings.data_dir) / "alerts")
        _alert_service = AlertService(store)
    return _alert_service


_watchlist_store: WatchlistStore | None = None


def watchlist_store() -> WatchlistStore:
    global _watchlist_store
    if _watchlist_store is None:
        _watchlist_store = WatchlistStore(Path(settings.data_dir) / "watchlists")
    return _watchlist_store


_agent_service: AgentService | None = None


def _agent_reviewer(summary: str) -> str:
    """Groq first (free 14k/day), Gemini Flash fallback. Empty when unconfigured."""
    from modules.ai_agent.prompts import load_prompt

    prompt = load_prompt("review", summary=summary)
    if settings.groq_api_key:
        try:
            return GroqProvider(settings.groq_api_key).generate(prompt)
        except Exception:
            pass
    if settings.gemini_api_key:
        try:
            return GeminiProvider(settings.gemini_api_key).generate(prompt)
        except Exception:
            pass
    return ""


def agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        store = AgentBacktestStore(Path(settings.data_dir) / "agent")
        parser = None
        if settings.cloudflare_ai_url and settings.cloudflare_ai_token:
            parser = CloudflareParser(settings.cloudflare_ai_url, settings.cloudflare_ai_token)
        cache = TtlCache(ttl_seconds=24 * 60 * 60, redis_url=settings.redis_url)
        _agent_service = AgentService(
            store, parser=parser, reviewer=_agent_reviewer, cache=cache
        )
    return _agent_service
