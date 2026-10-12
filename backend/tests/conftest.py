import os
import tempfile

# Must be set before the app is imported: settings are read at import time.
TMP_DIR = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DIR}/test.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"
os.environ["UPLOAD_DIR"] = f"{TMP_DIR}/uploads"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Business, Message, Ticket, User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "password123"
PASSWORD_HASH = hash_password(PASSWORD)  # hashed once: bcrypt is slow on purpose


@pytest.fixture(autouse=True)
def fresh_db():
    from app.routers.auth import reset_rate_limiter

    reset_rate_limiter()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client():
    # The "with" block keeps one event loop for HTTP calls and WebSockets in the same test.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def world() -> dict:
    """Businesses "a" and "b", each with admin, agent, customer1, customer2
    and one ticket owned by customer1. Returns the ids."""
    result = {}
    with SessionLocal() as db:
        for key in ("a", "b"):
            business = Business(name=f"Business {key}", slug=f"business-{key}")
            users = {
                name: User(
                    business=business,
                    name=f"{name} {key}",
                    email=f"{name}@{key}.example.com",
                    password_hash=PASSWORD_HASH,
                    role=role,
                )
                for name, role in [
                    ("admin", "admin"),
                    ("agent", "agent"),
                    ("customer1", "customer"),
                    ("customer2", "customer"),
                ]
            }
            db.add_all(users.values())
            db.flush()
            ticket = Ticket(
                business_id=business.id,
                customer_id=users["customer1"].id,
                subject=f"Ticket {key}",
                category="general",
                priority="low",
            )
            db.add(ticket)
            db.flush()
            db.add(Message(ticket_id=ticket.id, sender_id=users["customer1"].id, body="hello"))
            db.commit()
            result[key] = {name: user.id for name, user in users.items()} | {"ticket": ticket.id}
    return result
