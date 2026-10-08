from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession
from app.models import User
from app.schemas import AccessTokenOut, LoginIn, MeOut, RefreshIn, RegisterBusinessIn, TokenOut
from app.security import create_token, decode_token
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def issue_tokens(user: User) -> TokenOut:
    return TokenOut(access_token=create_token(user.id, "access"), refresh_token=create_token(user.id, "refresh"))


@router.post("/register-business", response_model=TokenOut, status_code=201)
def register_business(data: RegisterBusinessIn, db: DbSession):
    return issue_tokens(auth_service.register_business(db, data))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: DbSession):
    return issue_tokens(auth_service.authenticate(db, data.email, data.password))


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(data: RefreshIn, db: DbSession):
    user_id = decode_token(data.refresh_token, "refresh")
    if user_id is None or db.get(User, user_id) is None:
        raise HTTPException(401, "Invalid refresh token")
    return AccessTokenOut(access_token=create_token(user_id, "access"))


@router.get("/me", response_model=MeOut)
def me(user: CurrentUser):
    return user
