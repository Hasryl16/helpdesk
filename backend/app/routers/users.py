from fastapi import APIRouter

from app.deps import AdminUser, DbSession
from app.schemas import UserCreateIn, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(admin: AdminUser, db: DbSession):
    return auth_service.list_users(db, admin)


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreateIn, admin: AdminUser, db: DbSession):
    return auth_service.create_user(db, admin, data)
