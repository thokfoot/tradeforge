from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.api import deps
from modules.shared.contracts import User

router = APIRouter(prefix="/api/assistant")


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
def chat(
    req: ChatRequest, user: User = Depends(deps.require_plan("pro"))
) -> dict:
    reply = deps.assistant_service().chat(req.user_id, req.message)
    return asdict(reply)


class ConfirmRequest(BaseModel):
    user_id: str
    action: str


@router.post("/confirm")
def confirm(req: ConfirmRequest) -> dict:
    ok = deps.assistant_service().confirm_action(req.user_id, req.action)
    if not ok:
        raise HTTPException(status_code=409, detail="no matching pending action")
    return {"confirmed": True}
