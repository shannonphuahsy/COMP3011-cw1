def test_nearby(client):
    r = client.get("/analytics/nearby", params={"lat": 53.800, "lon": -1.549, "radius": 500})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_ranked(client):
    r = client.get("/analytics/ranked", params={"city": "Leeds", "limit": 5})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    if r.json():
        assert "cyber_exposure_score" in r.json()[0]

def test_crime(client, any_wifi_id):
    r = client.get(f"/analytics/crime/{any_wifi_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["wifi_id"] == any_wifi_id
    assert "crime_last_12m" in body