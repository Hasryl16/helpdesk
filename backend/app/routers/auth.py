import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, Response

from app.config import settings
from app.deps import CurrentUser, DbSession
from app.models import User
from app.schemas import AccessTokenOut, LoginIn, MeOut, RefreshIn, RegisterBusinessIn, TokenOut
from app.security import create_token, decode_token
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_RATE_LIMIT_WINDOW = 60
LOGIN_RATE_LIMIT_MAX = 5


def check_login_rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    now = time.time()
    attempts = [t for t in _login_attempts[ip] if now - t < LOGIN_RATE_LIMIT_WINDOW]
    if len(attempts) >= LOGIN_RATE_LIMIT_MAX:
        raise HTTPException(429, "Too many login attempts. Please try again later.")
    attempts.append(now)
    _login_attempts[ip] = attempts


def reset_rate_limiter() -> None:
    _login_attempts.clear()


def issue_tokens(user: User) -> TokenOut:
    return TokenOut(access_token=create_token(user.id, "access"), refresh_token=create_token(user.id, "refresh"))


def set_token_cookies(response: Response, tokens: TokenOut) -> None:
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=settings.access_token_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=settings.refresh_token_days * 86400,
    )


@router.post("/register-business", response_model=TokenOut, status_code=201)
def register_business(response: Response, data: RegisterBusinessIn, db: DbSession):
    tokens = issue_tokens(auth_service.register_business(db, data))
    set_token_cookies(response, tokens)
    return tokens


@router.post("/login", response_model=TokenOut)
def login(request: Request, response: Response, data: LoginIn, db: DbSession):
    check_login_rate_limit(request)
    tokens = issue_tokens(auth_service.authenticate(db, data.email, data.password))
    set_token_cookies(response, tokens)
    return tokens


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(request: Request, response: Response, db: DbSession, data: RefreshIn | None = None):
    refresh_token = data.refresh_token if data and data.refresh_token else request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "Invalid refresh token")
    user_id = decode_token(refresh_token, "refresh")
    if user_id is None or db.get(User, user_id) is None:
        raise HTTPException(401, "Invalid refresh token")
    access_token = create_token(user_id, "access")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=settings.access_token_minutes * 60,
    )
    return AccessTokenOut(access_token=access_token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}


@router.get("/ws-token")
def ws_token(user: CurrentUser):
    return {"token": create_token(user.id, "access")}


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser):
    return user
