def test_openapi_contract_has_expected_paths(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    paths = spec.get("paths", {})
    # Check a few critical routes exist
    for path in [
        "/incidents/",
        "/incidents/{incident_id}",
        "/incidents/{wifi_id}",
        "/analytics/nearby",
        "/analytics/ranked",
        "/analytics/crime/{wifi_id}",
        "/assessments/safety",
        "/hotspots/{wifi_id}",
        "/hotspots/{wifi_id}/status",
        "/hotspots/{wifi_id}/security",
        "/healthz",
    ]:
        assert path in paths, f"Missing path in OpenAPI: {path}"