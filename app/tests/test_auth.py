# tests/test_auth.py

def test_signup_and_login(client):
    email = "test_auth_user@example.com"
    password = "abc12345"

    # Cleanup is handled by conftest cleanup fixture

    # Signup (idempotent)
    r = client.post(f"/auth/signup?email={email}&password={password}")
    assert r.status_code in (200, 409)

    # Login
    r = client.post(f"/auth/login?email={email}&password={password}")
    assert r.status_code == 200
    assert "access_token" in r.json()