# tests/conftest.py
import os
import contextlib
import pytest
import asyncpg
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app

# ---------- Sync client (for most tests) ----------
@pytest.fixture(scope="session")
def client():
    return TestClient(app)

# ---------- Async client (when you want async tests) ----------
@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# ---------- Per-test asyncpg connection (function scope) ----------
@pytest.fixture
async def pg_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL not set; skipping DB-dependent tests")
    conn = await asyncpg.connect(dsn)
    try:
        yield conn
    finally:
        await conn.close()

# ---------- Helper: fetch any wifi_id from the enriched view ----------
@pytest.fixture
async def any_wifi_id(pg_conn):
    row = await pg_conn.fetchrow("SELECT wifi_id FROM api.api_wifi_hotspot_risk LIMIT 1;")
    if not row:
        pytest.skip("No rows in api.api_wifi_hotspot_risk; seed test data first")
    return row["wifi_id"]

# ---------- Helper: ensure a mapped BSSID exists and remove it afterwards ----------
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

# ---------- Safe patch rollback for hotspot fields (function-scoped connection) ----------
@contextlib.asynccontextmanager
async def _backup_and_restore(conn, wifi_id, field):
    row = await conn.fetchrow(f"SELECT {field} FROM core.core_wifi_hotspot WHERE wifi_id=$1;", wifi_id)
    if not row:
        pytest.skip(f"wifi_id {wifi_id} not found in core.core_wifi_hotspot")
    before = row[field]
    try:
        yield before
    finally:
        await conn.execute(f"UPDATE core.core_wifi_hotspot SET {field}=$2 WHERE wifi_id=$1;", wifi_id, before)

@pytest.fixture
def restore_helper(pg_conn):
    def maker(wifi_id, field):
        return _backup_and_restore(pg_conn, wifi_id, field)
    return maker