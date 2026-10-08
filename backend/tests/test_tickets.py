from tests.utils import auth_header

NEW_TICKET = {"subject": "Printer rusak", "category": "hardware", "priority": "high", "message": "Tidak bisa print"}


def test_customer_creates_ticket_with_first_message(client, world):
    headers = auth_header(world["a"]["customer2"])
    res = client.post("/tickets", headers=headers, json=NEW_TICKET)
    assert res.status_code == 201
    ticket = res.json()
    assert ticket["status"] == "open"
    assert ticket["assigned_agent"] is None

    messages = client.get(f"/tickets/{ticket['id']}/messages", headers=headers).json()
    assert [m["body"] for m in messages] == ["Tidak bisa print"]
    assert messages[0]["sender"]["role"] == "customer"


def test_only_customers_create_tickets(client, world):
    for name in ("admin", "agent"):
        res = client.post("/tickets", headers=auth_header(world["a"][name]), json=NEW_TICKET)
        assert res.status_code == 403


def test_list_is_scoped_by_role(client, world):
    client.post("/tickets", headers=auth_header(world["a"]["customer2"]), json=NEW_TICKET)

    staff_ids = {t["id"] for t in client.get("/tickets", headers=auth_header(world["a"]["agent"])).json()}
    own_ids = {t["id"] for t in client.get("/tickets", headers=auth_header(world["a"]["customer1"])).json()}
    assert len(staff_ids) == 2  # both customers' tickets of business a
    assert own_ids == {world["a"]["ticket"]}


def test_list_filters_by_status_and_sorts_by_latest_activity(client, world):
    headers = auth_header(world["a"]["agent"])
    new_id = client.post("/tickets", headers=auth_header(world["a"]["customer2"]), json=NEW_TICKET).json()["id"]
    assert [t["id"] for t in client.get("/tickets", headers=headers).json()][0] == new_id

    client.patch(f"/tickets/{world['a']['ticket']}", headers=headers, json={"assigned_agent_id": world["a"]["agent"]})
    in_progress = client.get("/tickets?status=in_progress", headers=headers).json()
    assert [t["id"] for t in in_progress] == [world["a"]["ticket"]]
    assert client.get("/tickets?status=bogus", headers=headers).status_code == 422


def test_agent_takes_open_ticket_and_it_moves_to_in_progress(client, world):
    res = client.patch(
        f"/tickets/{world['a']['ticket']}",
        headers=auth_header(world["a"]["agent"]),
        json={"assigned_agent_id": world["a"]["agent"]},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"
    assert res.json()["assigned_agent"]["id"] == world["a"]["agent"]


def test_agent_cannot_assign_someone_else(client, world):
    res = client.patch(
        f"/tickets/{world['a']['ticket']}",
        headers=auth_header(world["a"]["agent"]),
        json={"assigned_agent_id": world["a"]["admin"]},
    )
    assert res.status_code == 403


def test_full_status_flow_and_reopen(client, world):
    ticket_url = f"/tickets/{world['a']['ticket']}"
    agent = auth_header(world["a"]["agent"])
    customer = auth_header(world["a"]["customer1"])

    assert client.patch(ticket_url, headers=agent, json={"status": "in_progress"}).status_code == 200
    # customer may not resolve
    assert client.patch(ticket_url, headers=customer, json={"status": "resolved"}).status_code == 403
    assert client.patch(ticket_url, headers=agent, json={"status": "resolved"}).status_code == 200
    # customer reopens a resolved ticket
    res = client.patch(ticket_url, headers=customer, json={"status": "open"})
    assert res.status_code == 200
    assert res.json()["status"] == "open"


def test_closed_is_final(client, world):
    ticket_url = f"/tickets/{world['a']['ticket']}"
    agent = auth_header(world["a"]["agent"])
    for status in ("in_progress", "resolved", "closed"):
        assert client.patch(ticket_url, headers=agent, json={"status": status}).status_code == 200

    res = client.patch(ticket_url, headers=agent, json={"status": "open"})
    assert res.status_code == 409
    res = client.patch(ticket_url, headers=agent, json={"assigned_agent_id": world["a"]["agent"]})
    assert res.status_code == 409  # a closed ticket cannot be reassigned either


def test_skipping_a_status_is_409(client, world):
    res = client.patch(
        f"/tickets/{world['a']['ticket']}", headers=auth_header(world["a"]["agent"]), json={"status": "closed"}
    )
    assert res.status_code == 409


def test_empty_patch_is_422(client, world):
    res = client.patch(f"/tickets/{world['a']['ticket']}", headers=auth_header(world["a"]["agent"]), json={})
    assert res.status_code == 422


def test_assign_plus_status_is_checked_against_the_original_status(client, world):
    ticket_url = f"/tickets/{world['a']['ticket']}"
    agent_id = world["a"]["agent"]
    headers = auth_header(agent_id)
    # open -> resolved would skip in_progress
    res = client.patch(ticket_url, headers=headers, json={"assigned_agent_id": agent_id, "status": "resolved"})
    assert res.status_code == 409
    res = client.patch(ticket_url, headers=headers, json={"assigned_agent_id": agent_id, "status": "in_progress"})
    assert res.status_code == 200


def test_admin_assigns_only_agents_of_own_business(client, world):
    ticket_url = f"/tickets/{world['a']['ticket']}"
    admin = auth_header(world["a"]["admin"])
    for not_an_agent in (world["a"]["admin"], world["a"]["customer2"]):
        assert client.patch(ticket_url, headers=admin, json={"assigned_agent_id": not_an_agent}).status_code == 404

    res = client.patch(ticket_url, headers=admin, json={"assigned_agent_id": world["a"]["agent"]})
    assert res.status_code == 200
    assert res.json()["assigned_agent"]["id"] == world["a"]["agent"]


def test_customer_cannot_assign(client, world):
    res = client.patch(
        f"/tickets/{world['a']['ticket']}",
        headers=auth_header(world["a"]["customer1"]),
        json={"assigned_agent_id": world["a"]["agent"]},
    )
    assert res.status_code == 403


def test_blank_ticket_fields_are_422(client, world):
    blank = {"subject": " ", "category": " ", "priority": "low", "message": "   "}
    res = client.post("/tickets", headers=auth_header(world["a"]["customer2"]), json=blank)
    assert res.status_code == 422
