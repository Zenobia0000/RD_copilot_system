"""JWT validation dependencies for Supabase Auth.

Usage — apply to a router that requires authentication:

    from fastapi import APIRouter, Depends
    from app.middleware.auth import get_current_user

    router = APIRouter(dependencies=[Depends(get_current_user)])
"""

from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.settings import settings

_bearer_scheme = HTTPBearer(auto_error=False)


_DEV_BYPASS_TOKEN = "dev-bypass-token"

_DEV_USER = {
    "sub": "dev-admin-00000000",
    "email": "admin@dev.local",
    "role": "authenticated",
}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """Require a valid Supabase JWT.  Returns the decoded payload as a dict
    containing at least ``sub``, ``email``, and ``role``.

    Raises 401 if the token is missing, expired, or invalid.

    In development mode (``jwt_secret`` not set), the special token
    ``dev-bypass-token`` is accepted and returns a mock user.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Dev bypass: only when debug mode AND jwt_secret is empty
    if settings.debug and not settings.jwt_secret and token == _DEV_BYPASS_TOKEN:
        return dict(_DEV_USER)

    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET not configured",
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "sub": payload.get("sub"),
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
    }


def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[dict]:
    """Same as ``get_current_user`` but returns ``None`` instead of raising
    when no token is provided.  Useful for endpoints that behave differently
    for authenticated vs. anonymous users.
    """
    if credentials is None:
        return None

    # Delegate to the strict version; if the token is present but invalid we
    # still want a 401.
    return get_current_user(credentials)
