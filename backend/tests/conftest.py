import os
import tempfile

# Must be set before the app is imported: settings are read at import time.
TMP_DIR = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DIR}/test.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"
os.environ["UPLOAD_DIR"] = f"{TMP_DIR}/uploads"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client():
    # The "with" block keeps one event loop for HTTP calls and WebSockets in the same test.
    with TestClient(app) as test_client:
        yield test_client
