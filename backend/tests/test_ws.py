import pytest
from starlette.websockets import WebSocketDisconnect

from app.security import create_token
from tests.utils import auth_header


def ws_url(ticket_id: int, user_id: int) -> str:
    return f"/ws/tickets/{ticket_id}?token={create_token(user_id, 'access')}"


def close_code(client, url: str) -> int:
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(url) as ws:
            ws.receive_json()
    return exc.value.code


def test_message_reaches_everyone_in_the_room_and_is_saved(client, world):
    ticket_id = world["a"]["ticket"]
    with (
        client.websocket_connect(ws_url(ticket_id, world["a"]["customer1"])) as customer,
        client.websocket_connect(ws_url(ticket_id, world["a"]["agent"])) as agent,
    ):
        customer.send_json({"body": "Halo, ada yang bisa bantu?"})
        for ws in (customer, agent):
            event = ws.receive_json()
            assert event["type"] == "message"
            assert event["message"]["body"] == "Halo, ada yang bisa bantu?"
            assert event["message"]["sender"]["role"] == "customer"

    history = client.get(f"/tickets/{ticket_id}/messages", headers=auth_header(world["a"]["agent"])).json()
    assert history[-1]["body"] == "Halo, ada yang bisa bantu?"


def test_status_change_is_pushed_to_the_room(client, world):
    ticket_id = world["a"]["ticket"]
    with client.websocket_connect(ws_url(ticket_id, world["a"]["customer1"])) as customer:
        client.patch(f"/tickets/{ticket_id}", headers=auth_header(world["a"]["agent"]), json={"status": "in_progress"})
        event = customer.receive_json()
        assert event["type"] == "ticket"
        assert event["ticket"]["status"] == "in_progress"


def test_closed_ticket_rejects_messages(client, world):
    ticket_id = world["a"]["ticket"]
    agent = auth_header(world["a"]["agent"])
    for status in ("in_progress", "resolved", "closed"):
        client.patch(f"/tickets/{ticket_id}", headers=agent, json={"status": status})

    with client.websocket_connect(ws_url(ticket_id, world["a"]["customer1"])) as ws:
        ws.send_json({"body": "masih ada?"})
        assert ws.receive_json() == {"type": "error", "message": "Ticket is closed"}


def test_empty_message_is_rejected(client, world):
    with client.websocket_connect(ws_url(world["a"]["ticket"], world["a"]["agent"])) as ws:
        ws.send_json({"body": "   "})
        assert ws.receive_json()["type"] == "error"


def test_no_or_bad_token_is_closed_with_4401(client, world):
    assert close_code(client, f"/ws/tickets/{world['a']['ticket']}") == 4401
    assert close_code(client, f"/ws/tickets/{world['a']['ticket']}?token=garbage") == 4401


def test_other_business_ticket_is_closed_with_4404(client, world):
    assert close_code(client, ws_url(world["b"]["ticket"], world["a"]["agent"])) == 4404


def test_other_customers_ticket_is_closed_with_4404(client, world):
    assert close_code(client, ws_url(world["a"]["ticket"], world["a"]["customer2"])) == 4404
