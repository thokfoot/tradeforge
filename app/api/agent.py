from __future__ import annotations

import threading
import time
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.api import deps
from modules.ai_agent.dsl import DslError, plan_text
from modules.shared.contracts import User

router = APIRouter(prefix="/api/agent")

PARSE_RATE_LIMIT = 20
PARSE_RATE_WINDOW_SECONDS = 60


class _RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            recent = [t for t in self._hits.get(key, []) if now - t < self._window]
            if len(recent) >= self._limit:
                self._hits[key] = recent
                return False
            recent.append(now)
            self._hits[key] = recent
            return True


_parse_limiter = _RateLimiter(PARSE_RATE_LIMIT, PARSE_RATE_WINDOW_SECONDS)


class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


class RunRequest(BaseModel):
    dsl: dict = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    backtest_id: str


class SuggestRequest(BaseModel):
    metrics: dict = Field(default_factory=dict)


@router.post("/parse")
def parse(
    req: ParseRequest,
    request: Request,
    user: User = Depends(deps.current_user),
) -> dict:
    ip = request.client.host if request.client else "unknown"
    if not _parse_limiter.allow(ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit: 20 requests/minute. Thoda ruk kar wapas try karo.",
        )
    try:
        dsl = deps.agent_service().parse(req.text)
    except DslError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "dsl": dsl,
        "plan_text": plan_text(dsl) if dsl.get("intent") != "review" else None,
    }


@router.post("/run")
def run(
    req: RunRequest,
    user: User = Depends(deps.current_user),
) -> dict:
    market = str(req.dsl.get("market") or "IN").upper()

    def fetch(symbol: str, interval: str, start, end):
        return deps.provider_for(market).fetch_ohlcv(
            symbol, interval, pd.Timestamp(start), pd.Timestamp(end)
        )

    try:
        return deps.agent_service().run(user.id, req.dsl, fetch)
    except DslError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/review")
def review(
    req: ReviewRequest,
    user: User = Depends(deps.current_user),
) -> dict:
    try:
        return deps.agent_service().review(user.id, req.backtest_id)
    except DslError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/history")
def history(
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(deps.current_user),
) -> dict:
    return {"records": deps.agent_service().history(user.id, limit)}


@router.post("/suggest")
def suggest(
    req: SuggestRequest,
    user: User = Depends(deps.current_user),
) -> dict:
    return {"chips": deps.agent_service().suggest(req.metrics)}
