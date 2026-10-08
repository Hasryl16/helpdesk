from tests.utils import auth_header

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def upload(client, ticket_id: int, user_id: int, content: bytes, name: str = "photo.png"):
    return client.post(
        f"/tickets/{ticket_id}/attachments",
        headers=auth_header(user_id),
        files={"file": (name, content, "image/png")},
    )


def test_upload_and_download_image(client, world):
    ticket_id = world["a"]["ticket"]
    res = upload(client, ticket_id, world["a"]["customer1"], PNG)
    assert res.status_code == 201
    message = res.json()
    assert message["has_attachment"] is True

    res = client.get(f"/tickets/{ticket_id}/attachments/{message['id']}", headers=auth_header(world["a"]["agent"]))
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert res.content == PNG


def test_non_image_is_422_even_with_image_content_type(client, world):
    res = upload(client, world["a"]["ticket"], world["a"]["customer1"], b"<script>alert(1)</script>", "x.png")
    assert res.status_code == 422


def test_too_large_is_413(client, world):
    res = upload(client, world["a"]["ticket"], world["a"]["customer1"], PNG + b"\x00" * (5 * 1024 * 1024))
    assert res.status_code == 413


def test_other_business_cannot_upload_or_download(client, world):
    ticket_id = world["b"]["ticket"]
    message_id = upload(client, ticket_id, world["b"]["customer1"], PNG).json()["id"]

    assert upload(client, ticket_id, world["a"]["customer1"], PNG).status_code == 404
    res = client.get(f"/tickets/{ticket_id}/attachments/{message_id}", headers=auth_header(world["a"]["admin"]))
    assert res.status_code == 404


def test_closed_ticket_rejects_upload(client, world):
    ticket_id = world["a"]["ticket"]
    agent = auth_header(world["a"]["agent"])
    for status in ("in_progress", "resolved", "closed"):
        client.patch(f"/tickets/{ticket_id}", headers=agent, json={"status": status})
    assert upload(client, ticket_id, world["a"]["customer1"], PNG).status_code == 409
