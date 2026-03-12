# app/db/models.py
from app.db.database import get_db


# ----------------------
# Hotspot Lookups
# ----------------------
async def get_hotspot_by_wifi_id(wifi_id: str):
    db = await get_db()
    row = await db.fetchrow("""
        SELECT *
        FROM api.api_wifi_hotspot_risk
        WHERE wifi_id = $1
    """, wifi_id)
    await db.close()
    return row


async def update_hotspot_status(wifi_id: str, status: str):
    db = await get_db()
    await db.execute("""
        UPDATE core.core_wifi_hotspot
        SET status = $2
        WHERE wifi_id = $1
    """, wifi_id, status)
    await db.close()


async def update_hotspot_security(wifi_id: str, sec: str):
    db = await get_db()
    await db.execute("""
        UPDATE core.core_wifi_hotspot
        SET security_protection = $2
        WHERE wifi_id = $1
    """, wifi_id, sec)
    await db.close()


# ----------------------
# BSSID → WiFi Lookup
# ----------------------
async def get_wifi_id_from_bssid(bssid: str):
    db = await get_db()
    row = await db.fetchrow("""
        SELECT wifi_id
        FROM api.api_wifi_bssid_map
        WHERE bssid = $1
    """, bssid)
    await db.close()
    return row["wifi_id"] if row else None


# ----------------------
# Nearby Search
# ----------------------
async def get_hotspots_near(lat: float, lon: float, radius: int):
    db = await get_db()
    rows = await db.fetch("""
        WITH q AS (
            SELECT ST_SetSRID(ST_MakePoint($2,$1),4326)::geography AS g
        )
        SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
        FROM api.api_wifi_hotspot_risk h, q
        WHERE ST_DWithin(h.geom_geog, q.g, $3)
        ORDER BY dist ASC
        LIMIT 50
    """, lat, lon, radius)
    await db.close()
    return rows


# ----------------------
# Ranking
# ----------------------
async def get_ranked_hotspots(city: str, limit: int = 50):
    db = await get_db()
    rows = await db.fetch("""
        SELECT *
        FROM api.api_wifi_hotspot_risk
        WHERE LOWER(city) = LOWER($1)
        ORDER BY cyber_exposure_score DESC
        LIMIT $2
    """, city, limit)
    await db.close()
    return rows


# ----------------------
# Crime lookups (Materialized View)
# ----------------------
async def get_crime_count(wifi_id: str):
    db = await get_db()
    row = await db.fetchrow("""
        SELECT crime_12m_count
        FROM api.api_hotspot_crime_12m_500m
        WHERE wifi_id = $1
    """, wifi_id)
    await db.close()
    return row["crime_12m_count"] if row else 0


# ----------------------
# Incidents CRUD
# ----------------------
async def create_incident(wifi_id: str, bssid: str, desc: str):
    db = await get_db()
    row = await db.fetchrow("""
        INSERT INTO api.api_user_incidents (wifi_id, bssid, description)
        VALUES ($1, $2, $3)
        RETURNING *
    """, wifi_id, bssid, desc)
    await db.close()
    return row


async def list_incidents(wifi_id: str):
    db = await get_db()
    rows = await db.fetch("""
        SELECT *
        FROM api.api_user_incidents
        WHERE wifi_id = $1
        ORDER BY created_at DESC
    """, wifi_id)
    await db.close()
    return rows


async def delete_incident(incident_id: int):
    db = await get_db()
    await db.execute("""
        DELETE FROM api.api_user_incidents
        WHERE id = $1
    """, incident_id)
    await db.close()