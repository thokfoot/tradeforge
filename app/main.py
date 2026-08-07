import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.backtest import router as backtest_router
from app.api.export import router as export_router
from app.api.health import router as health_router
from app.api.journal import router as journal_router
from app.api.market import router as market_router
from app.api.paper import router as paper_router
from app.api.screener import router as screener_router
from app.api.strategies import router as strategies_router
from app.config import settings


async def _alert_loop():
    from app.api import deps

    while True:
        try:
            deps.alert_service().check_all(deps.provider_for)
        except Exception:
            pass
        await asyncio.sleep(settings.alert_check_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if settings.alerts_enabled:
        task = asyncio.create_task(_alert_loop())
    yield
    if task is not None:
        task.cancel()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(market_router)
app.include_router(backtest_router)
app.include_router(paper_router)
app.include_router(strategies_router)
app.include_router(assistant_router)
app.include_router(auth_router)
app.include_router(screener_router)
app.include_router(journal_router)
app.include_router(export_router)
app.include_router(alerts_router)
