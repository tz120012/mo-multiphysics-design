"""Auth stubs: login / logout / me (Q1 placeholder)."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import require_bearer, user_from_token
from app.schemas.common import LoginRequest, LoginResponse, MeResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login stub (Q1)",
    description="Any non-empty username+password yields a placeholder Bearer token.",
)
def login(body: LoginRequest) -> LoginResponse:
    if not body.username.strip() or not body.password.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "username and password required"},
        )
    # Token embeds username so /me can recover it without a session store.
    token = f"{body.username.strip()}:{uuid4().hex}"
    return LoginResponse(accessToken=token, tokenType="Bearer")


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout stub (Q1)",
)
def logout(_: Annotated[str, Depends(require_bearer)]) -> None:
    return None


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user stub (Q1)",
)
def me(token: Annotated[str, Depends(require_bearer)]) -> MeResponse:
    user = user_from_token(token)
    return MeResponse(**user)
