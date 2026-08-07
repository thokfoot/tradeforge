from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.api import deps
from modules.shared.contracts import Strategy, StrategyConfig, User

router = APIRouter(prefix="/api/strategies")


class SaveStrategyRequest(BaseModel):
    id: str
    version: str = ""
    author_user_id: str = "api"
    code: str
    params: dict = {}
    config: dict = {}
    data_version: str = "v1"


@router.post("/save")
def save_strategy(
    req: SaveStrategyRequest, user: User = Depends(deps.require_plan("pro"))
) -> dict:
    strategy = Strategy(
        id=req.id,
        version=req.version,
        author_user_id=user.id,
        code=req.code,
        params=req.params,
        config=StrategyConfig(**req.config),
        data_version=req.data_version,
    )
    try:
        saved = deps.strategy_service().save(strategy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return asdict(saved)


@router.get("/{strategy_id}/versions")
def list_versions(strategy_id: str) -> list[str]:
    return deps.strategy_service().list_versions(strategy_id)


class ValidateRequest(BaseModel):
    code: str
    params: dict = {}


@router.post("/validate")
def validate_strategy(req: ValidateRequest) -> dict:
    from modules.shared.contracts import ValidationResult

    result = deps.strategy_service().validate(
        Strategy(
            id="adhoc",
            version="",
            author_user_id="api",
            code=req.code,
            params=req.params,
            config=StrategyConfig(),
        )
    )
    return asdict(result)
