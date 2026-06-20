from __future__ import annotations

from dataclasses import dataclass
from fastapi import Header, HTTPException, status

from src.config import get_settings


@dataclass
class CurrentUser:
    role: str
    api_key_name: str


def resolve_user(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> CurrentUser:
    settings = get_settings()

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header.",
        )

    if x_api_key == settings.admin_api_key:
        return CurrentUser(role="admin", api_key_name="ADMIN_API_KEY")
    if x_api_key == settings.analyst_api_key:
        return CurrentUser(role="analyst", api_key_name="ANALYST_API_KEY")
    if x_api_key == settings.viewer_api_key:
        return CurrentUser(role="viewer", api_key_name="VIEWER_API_KEY")

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key.",
    )


def require_roles(user: CurrentUser, allowed: set[str]) -> None:
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' cannot perform this action. Allowed roles: {sorted(allowed)}",
        )
