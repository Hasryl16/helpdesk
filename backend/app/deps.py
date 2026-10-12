from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_token

DbSession = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: DbSession,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    user_id = decode_token(token, "access") if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Your role is not allowed to do this")
        return user

    return check


AdminUser = Annotated[User, Depends(require_role("admin"))]
CustomerUser = Annotated[User, Depends(require_role("customer"))]
