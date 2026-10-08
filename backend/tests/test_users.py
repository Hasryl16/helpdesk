from tests.utils import auth_header

NEW_AGENT = {"name": "New Agent", "email": "new@a.example.com", "password": "password123", "role": "agent"}


def test_admin_creates_user_in_own_business(client, world):
    headers = auth_header(world["a"]["admin"])
    res = client.post("/users", headers=headers, json=NEW_AGENT)
    assert res.status_code == 201
    assert "password_hash" not in res.json()

    emails = {user["email"] for user in client.get("/users", headers=headers).json()}
    assert "new@a.example.com" in emails
    assert "admin@b.example.com" not in emails  # never another business's users


def test_admin_cannot_create_another_admin(client, world):
    res = client.post("/users", headers=auth_header(world["a"]["admin"]), json=NEW_AGENT | {"role": "admin"})
    assert res.status_code == 422


def test_agent_and_customer_cannot_manage_users(client, world):
    for name in ("agent", "customer1"):
        headers = auth_header(world["a"][name])
        assert client.get("/users", headers=headers).status_code == 403
        assert client.post("/users", headers=headers, json=NEW_AGENT).status_code == 403
