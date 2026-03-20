def test_openapi_contract_has_expected_paths(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"].keys()

    expected_paths = [
        "/hotspots/{wifi_id}/status",
        "/hotspots/{wifi_id}/security",
        "/assessments/safety",
    ]

    for path in expected_paths:
        assert path in paths, f"Missing path in OpenAPI schema: {path}"