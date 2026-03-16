# app/db/models.py

from typing import Any, Dict, List, Optional
from app.db.database import get_db


# ============================================================
# BSSID → WiFi lookup
# ============================================================
async def get_wifi_id_from_bssid(bssid: str) -> Optional[str]:
    """
    Resolve a BSSID (AP MAC) to the owning wifi_id.

    Returns:
        wifi_id (str) if found, else None.
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            SELECT wifi_id
            FROM api.api_wifi_bssid_map
            WHERE bssid = $1
            """,
            bssid,
        )
        return row["wifi_id"] if row else None
    finally:
        await db.close()


# ============================================================
# Hotspot lookups / updates
# ============================================================
async def get_hotspot_by_wifi_id(wifi_id: str):
    """
    Return the enriched hotspot record (from view api.api_wifi_hotspot_risk) for a wifi_id.

    Returns:
        asyncpg.Record or None
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            SELECT *
            FROM api.api_wifi_hotspot_risk
            WHERE wifi_id = $1
            """,
            wifi_id,
        )
        return row
    finally:
        await db.close()


async def update_hotspot_status(wifi_id: str, status: str) -> None:
    """
    Update hotspot.status in the core table.
    """
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE core.core_wifi_hotspot
            SET status = $2
            WHERE wifi_id = $1
            """,
            wifi_id,
            status,
        )
    finally:
        await db.close()


async def update_hotspot_security(wifi_id: str, sec: str) -> None:
    """
    Update hotspot.security_protection in the core table.
    """
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE core.core_wifi_hotspot
            SET security_protection = $2
            WHERE wifi_id = $1
            """,
            wifi_id,
            sec,
        )
    finally:
        await db.close()


# ============================================================
# Crime context
# ============================================================
async def get_crime_count(wifi_id: str) -> int:
    """
    Return crime_12m_count for a wifi_id (0 if none).
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            SELECT crime_12m_count
            FROM api.api_hotspot_crime_12m_500m
            WHERE wifi_id = $1
            """,
            wifi_id,
        )
        return int(row["crime_12m_count"]) if row and row["crime_12m_count"] is not None else 0
    finally:
        await db.close()


# ============================================================
# Incidents (CRUD)
# ============================================================
async def create_incident(wifi_id: str, bssid: str, desc: str):
    """
    Insert a user-reported incident and return the inserted row.

    Returns:
        asyncpg.Record
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            INSERT INTO api.api_user_incidents (wifi_id, bssid, description)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            wifi_id,
            bssid,
            desc,
        )
        return row
    finally:
        await db.close()


async def update_incident(incident_id: int, description: str):
    """
    Update an incident's description and return the updated row.

    Returns:
        asyncpg.Record or None
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            UPDATE api.api_user_incidents
            SET description = $2
            WHERE id = $1
            RETURNING *
            """,
            incident_id,
            description,
        )
        return row
    finally:
        await db.close()


async def list_incidents(wifi_id: str):
    """
    List incidents for a wifi_id (newest first).

    Returns:
        List[asyncpg.Record]
    """
    db = await get_db()
    try:
        rows = await db.fetch(
            """
            SELECT *
            FROM api.api_user_incidents
            WHERE wifi_id = $1
            ORDER BY created_at DESC
            """,
            wifi_id,
        )
        return rows
    finally:
        await db.close()


async def delete_incident(incident_id: int) -> None:
    """
    Delete an incident by id.
    """
    db = await get_db()
    try:
        await db.execute(
            """
            DELETE FROM api.api_user_incidents
            WHERE id = $1
            """,
            incident_id,
        )
    finally:
        await db.close()


# ============================================================
# Proximity / Discovery
# ============================================================
async def get_hotspots_near(lat: float, lon: float, radius: int):
    """
    Radius search using ST_DWithin; returns up to 50 hotspots ordered by distance.

    Returns:
        List[asyncpg.Record]
    """
    db = await get_db()
    try:
        rows = await db.fetch(
            """
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
            FROM api.api_wifi_hotspot_risk h, q
            WHERE ST_DWithin(h.geom_geog, q.g, $3)
            ORDER BY dist ASC
            LIMIT 50
            """,
            lat,
            lon,
            radius,
        )
        return rows
    finally:
        await db.close()


async def get_ranked_hotspots(city: str, limit: int = 50):
    """
    Return hotspots in a city ranked by cyber_exposure_score (desc).

    Returns:
        List[asyncpg.Record]
    """
    db = await get_db()
    try:
        rows = await db.fetch(
            """
            SELECT *
            FROM api.api_wifi_hotspot_risk
            WHERE LOWER(city) = LOWER($1)
            ORDER BY cyber_exposure_score DESC
            LIMIT $2
            """,
            city,
            limit,
        )
        return rows
    finally:
        await db.close()


# ============================================================
# KNN (Top-K closest)
# ============================================================
async def get_hotspots_knn(lat: float, lon: float, k: int):
    """
    K-nearest hotspots (index-assisted ORDER BY <->). See that a GiST index exists on geography.

    Returns:
        List[asyncpg.Record]
    """
    db = await get_db()
    try:
        rows = await db.fetch(
            """
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT
                h.*,
                h.geom_geog <-> q.g AS dist
            FROM api.api_wifi_hotspot_risk h, q
            ORDER BY dist
            LIMIT $3;
            """,
            lat,   # $1
            lon,   # $2
            k,     # $3
        )
        return rows
    finally:
        await db.close()


# ============================================================
# Resolution helpers for /assessments/safety/current
# ============================================================
async def get_nearest_hotspot(lat: float, lon: float):
    """
    Nearest hotspot regardless of SSID (KNN).

    Returns:
        asyncpg.Record or None
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
            FROM api.api_wifi_hotspot_risk h, q
            ORDER BY h.geom_geog <-> q.g
            LIMIT 1;
            """,
            lat,
            lon,
        )
        return row
    finally:
        await db.close()


async def get_nearest_hotspot_by_ssid(lat: float, lon: float, ssid: str):
    """
    Nearest hotspot matching SSID (case-insensitive), using KNN.

    Returns:
        asyncpg.Record or None
    """
    db = await get_db()
    try:
        row = await db.fetchrow(
            """
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
            FROM api.api_wifi_hotspot_risk h, q
            WHERE h.name ILIKE $3
            ORDER BY h.geom_geog <-> q.g
            LIMIT 1;
            """,
            lat,
            lon,
            ssid,
        )
        return row
    finally:
        await db.close()


# ============================================================
# Simple spoof-risk heuristic (placeholder)
# ============================================================
async def detect_basic_spoof_risk(
    wifi_id: str,
    bssid: str,  # currently unused but kept for future OUI/scan-list checks
    ssid: Optional[str] = None,
    rssi: Optional[int] = None,
) -> bool:
    """
    Minimal heuristic:
    - If an SSID is supplied and equals the official hotspot name,
      and the measured RSSI is extremely strong (>-35 dBm), flag mild suspicion.
    - Intended as a placeholder until you add a scan-list and OUI checks.

    Returns:
        True if suspicious, else False.
    """
    hotspot = await get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        return False

    # asyncpg Record field access
    official_name = (hotspot["name"] or "").strip() if "name" in hotspot else ""
    if ssid and official_name and ssid.strip() == official_name and rssi is not None:
        if rssi > -35:
            return True
    return False