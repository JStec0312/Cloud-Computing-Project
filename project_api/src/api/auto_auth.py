# api/dependencies/auth.py
import logging
from fastapi import Depends, Request, Response, HTTPException, status
from src.application.errors import (InvalidCredentialsError, MissingAccessTokenError,
    RefreshTokenError)
    
from src.infrastructure.uow import SqlAlchemyUoW
from src.deps import get_auth_service, get_uow
from src.application.auth_service import AuthService
from src.config.app_config import settings
from src.domain.entities.user import User
import re
from src.api.schemas.users import UserFromToken
logger = logging.getLogger(__name__)

_BEARER_RE = re.compile(r"^\s*Bearer\s+(.+)$", re.IGNORECASE)

def get_bearer_token(request: Request) -> str | None:
    raw = request.headers.get("Authorization") or ""
    m = _BEARER_RE.match(raw)
    return m.group(1).strip() if m else None

async def current_user(
    request: Request,
    response: Response,
    uow: SqlAlchemyUoW = Depends(get_uow),
    auth: AuthService = Depends(get_auth_service),
) -> UserFromToken:
    access = get_bearer_token(request)
    refresh = (request.cookies.get(settings.refresh_cookie_name) or "").strip('"').strip()

    try:
        if access:
            user, new_access, maybe_new_refresh = await auth.auto_authenticate(
                uow=uow, access_token=access, refresh_token=refresh or None
            )
            if new_access and new_access != access:
                # (opcjonalnie) możesz dołożyć nagłówek z nowym access, jeśli front tak lubi
                response.headers["X-New-Access-Token"] = new_access
        else:
            if not refresh:
                raise MissingAccessTokenError("No access cookie")
            user, new_access, maybe_new_refresh = await auth.refresh_tokens(
                uow=uow,
                token=refresh,
                ip=(request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "")),
                user_agent=request.headers.get("User-Agent", ""),
            )


        if maybe_new_refresh:
            response.set_cookie(
                key=settings.refresh_cookie_name,
                value=maybe_new_refresh,
                httponly=settings.httponly_cookie,
                secure=settings.secure_cookie,
                samesite=settings.samesite_cookie,  
                path="/",                           
                max_age=settings.max_age_cookie,     
                domain=getattr(settings, "cookie_domain", None) or None,
            )

        request.state.user = user
        return UserFromToken(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
        )

    except MissingAccessTokenError as e:
        logger.warning("missing access token: %s ip=%s", e, request.client.host if request.client else "-")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except InvalidCredentialsError as e:
        logger.warning("auth failed: %s ip=%s", e, request.client.host if request.client else "-")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except RefreshTokenError as e:
        logger.warning("refresh failed: %s ip=%s", e.detail, request.client.host if request.client else "-")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail)
