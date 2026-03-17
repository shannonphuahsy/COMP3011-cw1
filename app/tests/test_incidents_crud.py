# tests/test_incidents_crud.py

def test_create_read_update_delete_incident(client, any_wifi_id, auth_headers):
    payload = {
        "wifi_id": any_wifi_id,
        "bssid": "AA:BB:CC:DD:EE:01",
        "description": "Phishing captive portal"
    }

    # Create
    r = client.post("/incidents/", params=payload, headers=auth_headers)
    assert r.status_code == 201
    inc_id = r.json()["id"]

    # Read
    r = client.get(f"/incidents/{any_wifi_id}")
    assert inc_id in [i["id"] for i in r.json()]

    # Update
    r = client.patch(
        f"/incidents/{inc_id}",
        params={"description": "False alarm: maintenance"},
        headers=auth_headers
    )
    assert r.status_code == 200

    # Delete
    r = client.delete(f"/incidents/{inc_id}", headers=auth_headers)
    assert r.status_code == 204

    # Confirm deletion
    r = client.get(f"/incidents/{any_wifi_id}")
    assert inc_id not in [i["id"] for i in r.json()]