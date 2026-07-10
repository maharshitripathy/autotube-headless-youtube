"""Shared API dependencies (single-user local auth)."""
from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

_basic = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Single-user HTTP Basic auth for the local dashboard."""
    ok_user = secrets.compare_digest(credentials.username, settings.admin_username)
    ok_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
