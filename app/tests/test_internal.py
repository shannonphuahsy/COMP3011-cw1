# tests/test_internal.py

def test_internal_stats_is_accessible(client, internal_headers):
    """
    Fast and lightweight test that ensures:
    - endpoint exists
    - API key authentication works
    - JSON structure is correct
    """
    r = client.get("/internal/stats", headers=internal_headers)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, dict)

    # Only check for the presence of keys (do NOT check table sizes)
    assert "ok" in data
    assert "database" in data
    assert "uptime_seconds" in data


def test_internal_version_is_accessible(client, internal_headers):
    """
    Avoid heavy PostGIS/PostgreSQL operations.
    Only check that the endpoint responds correctly.
    """
    r = client.get("/internal/version", headers=internal_headers)
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, dict)

    assert "api_version" in data
    assert "postgres_version" in data
    assert "postgis_version" in data