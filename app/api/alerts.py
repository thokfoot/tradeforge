from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from modules.shared.contracts import User

router = APIRouter(prefix="/api/alerts")


class CreateAlertRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=40)
    market: Literal["IN", "US", "CRYPTO"]
    metric: Literal["PRICE", "RSI"]
    condition: Literal["ABOVE", "BELOW"]
    value: float


@router.post("")
def create_alert(
    req: CreateAlertRequest, user: User = Depends(deps.current_user)
) -> dict:
    try:
        rule = deps.alert_service().create_rule(
            user.id, req.symbol, req.market, req.metric, req.condition, req.value
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return asdict(rule)


@router.get("")
def list_alerts(user: User = Depends(deps.current_user)) -> list[dict]:
    return [asdict(r) for r in deps.alert_service().list_rules(user.id)]


@router.delete("/{rule_id}")
def delete_alert(rule_id: str, user: User = Depends(deps.current_user)) -> dict:
    deleted = deps.alert_service().delete_rule(user.id, rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="alert not found")
    return {"deleted": True}


@router.get("/notifications")
def list_notifications(user: User = Depends(deps.current_user)) -> list[dict]:
    return [asdict(n) for n in deps.alert_service().notifications(user.id)]


@router.post("/notifications/clear")
def clear_notifications(user: User = Depends(deps.current_user)) -> dict:
    return {"cleared": deps.alert_service().clear_notifications(user.id)}


@router.post("/check")
def check_alerts(user: User = Depends(deps.current_user)) -> dict:
    triggered = deps.alert_service().check_user(user.id, deps.provider_for)
    return {
        "triggered": len(triggered),
        "notifications": [asdict(n) for n in triggered],
    }
