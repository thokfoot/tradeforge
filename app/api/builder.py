from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from modules.shared.contracts import Strategy, StrategyConfig, User
from modules.strategy_builder import StrategyBuilder

router = APIRouter(prefix="/api/builder")


class Condition(BaseModel):
    indicator: str
    period: int | None = None
    op: str
    ref: str | None = None
    ref_period: int | None = None
    value: float | None = None


class Rule(BaseModel):
    op: str = "AND"
    conditions: list[Condition] = []


class GenerateRequest(BaseModel):
    name: str = Field("", max_length=80)
    entry: Rule = Rule()
    exit: Rule = Rule()


@router.post("/generate")
def generate(
    req: GenerateRequest, user: User = Depends(deps.require_plan("pro"))
) -> dict:
    spec = {
        "entry": req.entry.model_dump(),
        "exit": req.exit.model_dump(),
    }
    builder = StrategyBuilder()
    errors = builder.validate(spec)
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))
    try:
        code = builder.generate(spec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    probe = Strategy(
        id="builder-probe",
        version="v0",
        author_user_id=user.id,
        code=code,
        config=StrategyConfig(),
    )
    validation = deps.strategy_service().validate(probe)
    return {
        "name": req.name,
        "code": code,
        "valid": validation.ok,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }
