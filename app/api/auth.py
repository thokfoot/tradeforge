from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from app.api import deps
from modules.shared.contracts import User

router = APIRouter(prefix="/api/auth")


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SubscribeRequest(BaseModel):
    plan: Literal["free", "pro"]


@router.post("/register")
def register(req: RegisterRequest) -> dict:
    try:
        user = deps.auth_service().register(req.email, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    session = deps.auth_service().login(req.email, req.password)
    return {"user": asdict(user), "token": session.token}


@router.post("/login")
def login(req: LoginRequest) -> dict:
    try:
        session = deps.auth_service().login(req.email, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    user = deps.auth_service().get_user(session.user_id)
    return {"user": asdict(user), "token": session.token}


@router.post("/subscribe")
def subscribe(
    req: SubscribeRequest, user: User = Depends(deps.require_plan("free"))
) -> dict:
    try:
        updated = deps.auth_service().create_subscription(user.id, req.plan)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return asdict(updated)


@router.get("/me")
def me(user: User = Depends(deps.current_user)) -> dict:
    return asdict(user)
