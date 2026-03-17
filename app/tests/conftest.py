# tests/conftest.py

import os
import pytest
import asyncpg
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app
import contextlib


API_KEY = os.getenv("API_KEY")

TEST_USERS = [
    "testuser@example.com",
    "testasync@example.com",
    "test_auth_user@example.com",
]


# -------------------------------
# Sync client
# -------------------------------
@pytest.fixture(scope="session")
def client():
    return TestClient(app)


# -------------------------------
# Async client
# -------------------------------
@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# -------------------------------
# DB connection
# -------------------------------
@pytest.fixture
async def pg_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL not set.")

    conn = await asyncpg.connect(dsn)
    try:
        yield conn
    finally:
        await conn.close()


# -------------------------------
# CLEANUP BEFORE EVERY TEST
# -------------------------------
@pytest.fixture(autouse=True)
async def cleanup_users(pg_conn):
    """Remove test users before every test to avoid unique errors."""
    for email in TEST_USERS:
        await pg_conn.execute("DELETE FROM auth_user WHERE email=$1;", email)
    yield
    for email in TEST_USERS:
        await pg_conn.execute("DELETE FROM auth_user WHERE email=$1;", email)


# -------------------------------
# wifi_id
# -------------------------------
@pytest.fixture
async def any_wifi_id(pg_conn):
    row = await pg_conn.fetchrow(
        "SELECT wifi_id FROM api.api_wifi_hotspot_risk LIMIT 1;"
    )
    if not row:
        pytest.skip("Seed data missing")
    return row["wifi_id"]


# -------------------------------
# mapped BSSID
# -------------------------------
@pytest.fixture
async def mapped_bssid(pg_conn, any_wifi_id):
    bssid = "AA:BB:CC:DD:EE:99"
    await pg_conn.execute("""
        INSERT INTO api.api_wifi_bssid_map (bssid, wifi_id)
        VALUES ($1, $2)
        ON CONFLICT (bssid) DO UPDATE SET wifi_id = EXCLUDED.wifi_id;
    """, bssid, any_wifi_id)

    try:
        yield bssid
    finally:
        await pg_conn.execute("DELETE FROM api.api_wifi_bssid_map WHERE bssid=$1;", bssid)


# -------------------------------
# AUTH FIXTURES (NO duplicates)
# -------------------------------
@pytest.fixture
def auth_headers(client):
    email = "testuser@example.com"
    password = "secret123"

    client.post(f"/auth/signup?email={email}&password={password}")
    r = client.post(f"/auth/login?email={email}&password={password}")
    token = r.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_async(async_client):
    email = "testasync@example.com"
    password = "secret123"

    await async_client.post(f"/auth/signup?email={email}&password={password}")
    r = await async_client.post(f"/auth/login?email={email}&password={password}")
    token = r.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


# -------------------------------
# API key
# -------------------------------
@pytest.fixture
def internal_headers():
    return {"X-API-Key": API_KEY}


# -------------------------------
# PATCH backup/restore
# -------------------------------
@contextlib.asynccontextmanager
async def _backup_and_restore(conn, wifi_id, field):
    row = await conn.fetchrow(
        f"SELECT {field} FROM core.core_wifi_hotspot WHERE wifi_id=$1;", wifi_id
    )
    before = row[field]
    try:
        yield before
    finally:
        await conn.execute(
            f"UPDATE core.core_wifi_hotspot SET {field}=$2 WHERE wifi_id=$1;",
            wifi_id,
            before
        )


@pytest.fixture
def restore_helper(pg_conn):
    def maker(wifi_id, field):
        return _backup_and_restore(pg_conn, wifi_id, field)
    return maker