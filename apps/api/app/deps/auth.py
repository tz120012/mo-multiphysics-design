"""Bearer token auth placeholder (no real user store in Q1)."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid5, NAMESPACE_URL

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def _error_detail(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


async def require_bearer(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
) -> str:
    """Require Authorization: Bearer <non-empty>. Any non-empty token passes."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_error_detail("unauthorized", "Missing or invalid Authorization header"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_error_detail("unauthorized", "Empty bearer token"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def user_from_token(token: str) -> dict[str, Any]:
    """Derive a stub user from the bearer token (Q1 placeholder)."""
    username = token.split(":", 1)[0] if ":" in token else (token[:32] or "user")
    uid = str(uuid5(NAMESPACE_URL, f"mo-user:{username}"))
    return {
        "id": uid,
        "username": username,
        "displayName": username,
    }
