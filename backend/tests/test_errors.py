def test_unknown_route_uses_json_error_format(client):
    res = client.get("/does-not-exist")
    assert res.status_code == 404
    assert res.json() == {"error": {"status": 404, "message": "Not Found"}}
