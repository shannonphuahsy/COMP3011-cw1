# app/db/models.py

from typing import Any, Dict, List, Optional
from app.db.database import get_db
from app.services.scoring import compute_score  # NEW

# ============================================================
# BSSID → WiFi lookup
# ============================================================

async def get_wifi_id_from_bssid(bssid: str) -> Optional[str]:
    db = await get_db()
    try:
        row = await db.fetchrow(
            "SELECT wifi_id FROM api.api_wifi_bssid_map WHERE bssid = $1",
            bssid,
        )
        return row["wifi_id"] if row else None
    finally:
        await db.close()


# ============================================================
# Hotspot lookups / updates
# ============================================================

async def get_hotspot_by_wifi_id(wifi_id: str):
    db = await get_db()
    try:
        row = await db.fetchrow(
            "SELECT * FROM api.api_wifi_hotspot_risk WHERE wifi_id = $1",
            wifi_id,
        )
        return row
    finally:
        await db.close()


async def update_hotspot_status(wifi_id: str, status: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE core.core_wifi_hotspot SET status = $2 WHERE wifi_id = $1",
            wifi_id,
            status,
        )
    finally:
        await db.close()


async def update_hotspot_security(wifi_id: str, sec: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE core.core_wifi_hotspot SET security_protection = $2 WHERE wifi_id = $1",
            wifi_id,
            sec,
        )
    finally:
        await db.close()


# ============================================================
# NEW: Cyber Exposure Score update
# ============================================================

async def update_cyber_score(wifi_id: str, score: int) -> None:
    """
    Updates cyber_exposure_score stored in the core table.
    """
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE core.core_wifi_hotspot
            SET cyber_exposure_score = $2
            WHERE wifi_id = $1
            """,
            wifi_id,
            score,
        )
    finally:
        await db.close()


# ============================================================
# NEW: Get ALL hotspots (for automated scoring)
# ============================================================

async def get_all_hotspots():
    db = await get_db()
    try:
        rows = await db.fetch("SELECT * FROM api.api_wifi_hotspot_risk")
        return rows
    finally:
        await db.close()


# ============================================================
# NEW: Recompute Cyber Scores (batch update)
# ============================================================

async def refresh_cyber_scores():
    """
    Recompute cyber_exposure_score for ALL hotspots using compute_score(),
    and update the core table.
    """
    hotspots = await get_all_hotspots()

    for hotspot in hotspots:
        wifi_id = hotspot["wifi_id"]

        # Crime + incidents
        crime = await get_crime_count(wifi_id)
        incidents = await list_incidents(wifi_id)

        # Compute dynamic score
        assessment = compute_score(
            hotspot=dict(hotspot),
            crime_count=crime,
            bssid="(system)",
            recent_incidents=[dict(i) for i in incidents],
            ssid=hotspot["name"],
            distance=None,
            client_hints=None,
        )

        # Save update
        await update_cyber_score(wifi_id, assessment.score)


# ============================================================
# Crime context
# ============================================================

async def get_crime_count(wifi_id: str) -> int:
    db = await get_db()
    try:
        row = await db.fetchrow(
            "SELECT crime_12m_count FROM api.api_hotspot_crime_12m_500m WHERE wifi_id = $1",
            wifi_id,
        )
        return int(row["crime_12m_count"]) if row and row["crime_12m_count"] is not None else 0
    finally:
        await db.close()


# ============================================================
# Incidents (CRUD)
# ============================================================

async def create_incident(wifi_id: str, bssid: str, desc: str):
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
    db = await get_db()
    try:
        rows = await db.fetch(
            "SELECT * FROM api.api_user_incidents WHERE wifi_id = $1 ORDER BY created_at DESC",
            wifi_id,
        )
        return rows
    finally:
        await db.close()


async def delete_incident(incident_id: int) -> None:
    db = await get_db()
    try:
        await db.execute("DELETE FROM api.api_user_incidents WHERE id = $1", incident_id)
    finally:
        await db.close()


# ============================================================
# Proximity / Discovery
# ============================================================

async def get_hotspots_near(lat: float, lon: float, radius: int):
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
# KNN (Top-K)
# ============================================================

async def get_hotspots_knn(lat: float, lon: float, k: int):
    db = await get_db()
    try:
        rows = await db.fetch(
            """
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT h.*, h.geom_geog <-> q.g AS dist
            FROM api.api_wifi_hotspot_risk h, q
            ORDER BY dist
            LIMIT $3;
            """,
            lat,
            lon,
            k,
        )
        return rows
    finally:
        await db.close()


# ============================================================
# Resolution Helpers
# ============================================================

async def get_nearest_hotspot(lat: float, lon: float):
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
# Spoof-risk heuristic
# ============================================================

async def detect_basic_spoof_risk(
    wifi_id: str,
    bssid: str,
    ssid: Optional[str] = None,
    rssi: Optional[int] = None,
) -> bool:
    hotspot = await get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        return False

    official_name = (hotspot["name"] or "").strip()

    if ssid and official_name and ssid.strip() == official_name and rssi is not None:
        if rssi > -35:
            return True

    return False