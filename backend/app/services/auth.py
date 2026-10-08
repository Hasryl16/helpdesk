import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Business, User
from app.schemas import RegisterBusinessIn, UserCreateIn
from app.security import hash_password, verify_password


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ensure_email_free(db: Session, email: str) -> None:
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Email already registered")


def register_business(db: Session, data: RegisterBusinessIn) -> User:
    slug = slugify(data.business_name)
    if not slug:
        raise HTTPException(422, "Business name must contain letters or numbers")
    if db.scalar(select(Business.id).where(Business.slug == slug)):
        raise HTTPException(409, "Business name already taken")
    email = data.email.lower()
    ensure_email_free(db, email)
    business = Business(name=data.business_name, slug=slug)
    admin = User(
        business=business,
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    return admin


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    # Same message for unknown email and wrong password, so emails can't be probed.
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return user


def list_users(db: Session, admin: User) -> list[User]:
    query = select(User).where(User.business_id == admin.business_id).order_by(User.id)
    return list(db.scalars(query))


def create_user(db: Session, admin: User, data: UserCreateIn) -> User:
    email = data.email.lower()
    ensure_email_free(db, email)
    user = User(
        business_id=admin.business_id,  # always the admin's own business, never from input
        name=data.name,
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    return user
