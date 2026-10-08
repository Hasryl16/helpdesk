from sqlalchemy import select

from app.db import SessionLocal
from app.models import User

NEW_BUSINESS = {
    "business_name": "Toko Baru",
    "name": "Owner",
    "email": "Owner@TokoBaru.com",
    "password": "password123",
}


def test_register_business_creates_admin_and_returns_tokens(client):
    res = client.post("/auth/register-business", json=NEW_BUSINESS)
    assert res.status_code == 201
    token = res.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["email"] == "owner@tokobaru.com"
    assert me["role"] == "admin"
    assert me["business"]["slug"] == "toko-baru"
    assert "password_hash" not in me


def test_password_is_stored_as_bcrypt_hash(client):
    client.post("/auth/register-business", json=NEW_BUSINESS)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "owner@tokobaru.com"))
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2b$")


def test_duplicate_email_is_409(client, world):
    res = client.post("/auth/register-business", json=NEW_BUSINESS | {"email": "admin@a.example.com"})
    assert res.status_code == 409
    assert res.json() == {"error": {"status": 409, "message": "Email already registered"}}


def test_duplicate_business_name_is_409(client):
    client.post("/auth/register-business", json=NEW_BUSINESS)
    res = client.post("/auth/register-business", json=NEW_BUSINESS | {"email": "other@tokobaru.com"})
    assert res.status_code == 409


def test_invalid_input_is_422_in_error_format(client):
    res = client.post("/auth/register-business", json=NEW_BUSINESS | {"email": "nope", "password": "short"})
    assert res.status_code == 422
    assert res.json()["error"]["message"] == "Validation error"


def test_login_then_refresh(client, world):
    res = client.post("/auth/login", json={"email": "agent@a.example.com", "password": "password123"})
    assert res.status_code == 200
    refresh_token = res.json()["refresh_token"]

    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    new_access = res.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 200


def test_wrong_password_is_401(client, world):
    res = client.post("/auth/login", json={"email": "agent@a.example.com", "password": "wrong-password"})
    assert res.status_code == 401


def test_refresh_token_is_not_an_access_token(client, world):
    tokens = client.post("/auth/login", json={"email": "agent@a.example.com", "password": "password123"}).json()
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert res.status_code == 401


def test_access_token_is_not_a_refresh_token(client, world):
    tokens = client.post("/auth/login", json={"email": "agent@a.example.com", "password": "password123"}).json()
    res = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert res.status_code == 401


def test_missing_or_garbage_token_is_401(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
