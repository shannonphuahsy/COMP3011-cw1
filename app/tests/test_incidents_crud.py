import pytest

def test_create_read_update_delete_incident(client, any_wifi_id):
    # Create
    payload = {
        "wifi_id": any_wifi_id,
        "bssid": "AA:BB:CC:DD:EE:01",
        "description": "Phishing captive portal"
    }
    r = client.post("/incidents/", json=payload)
    assert r.status_code == 201
    created = r.json()
    inc_id = created["id"]
    assert created["wifi_id"] == any_wifi_id
    assert created["description"] == payload["description"]

    # Read list
    r = client.get(f"/incidents/{any_wifi_id}")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert inc_id in ids

    # Update
    r = client.patch(f"/incidents/{inc_id}", json={"description": "False alarm: maintenance"})
    assert r.status_code == 200
    assert r.json()["description"] == "False alarm: maintenance"

    # Delete
    r = client.delete(f"/incidents/{inc_id}")
    assert r.status_code == 204

    # Confirm deletion
    r = client.get(f"/incidents/{any_wifi_id}")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert inc_id not in ids