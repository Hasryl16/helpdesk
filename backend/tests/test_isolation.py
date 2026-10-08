"""The checks a reviewer will try by hand: nobody reads another business's
(or another customer's) data, even by guessing ids."""

import pytest

from tests.utils import auth_header


@pytest.mark.parametrize("role", ["admin", "agent", "customer1"])
def test_other_business_ticket_is_404_everywhere(client, world, role):
    headers = auth_header(world["a"][role])
    ticket_id = world["b"]["ticket"]

    assert client.get(f"/tickets/{ticket_id}", headers=headers).status_code == 404
    assert client.get(f"/tickets/{ticket_id}/messages", headers=headers).status_code == 404
    res = client.patch(f"/tickets/{ticket_id}", headers=headers, json={"status": "in_progress"})
    assert res.status_code == 404


def test_list_never_contains_other_business_tickets(client, world):
    for role in ("admin", "agent", "customer1"):
        ids = {t["id"] for t in client.get("/tickets", headers=auth_header(world["a"][role])).json()}
        assert world["b"]["ticket"] not in ids


def test_customer_cannot_open_another_customers_ticket(client, world):
    headers = auth_header(world["a"]["customer2"])
    assert client.get(f"/tickets/{world['a']['ticket']}", headers=headers).status_code == 404
    assert client.get(f"/tickets/{world['a']['ticket']}/messages", headers=headers).status_code == 404


def test_admin_cannot_assign_agent_from_other_business(client, world):
    res = client.patch(
        f"/tickets/{world['a']['ticket']}",
        headers=auth_header(world["a"]["admin"]),
        json={"assigned_agent_id": world["b"]["agent"]},
    )
    assert res.status_code == 404
