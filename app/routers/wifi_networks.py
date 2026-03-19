# app/routers/wifi_networks.py

from fastapi import APIRouter, HTTPException, Query, Depends
from app.db import models
from app.db.database import get_db
from app.schemas.hotspot import Hotspot
from app.cache import cache_get, cache_setex
import json
from app.services.dependencies import require_user
from asyncpg import Connection  # type hint for the DB connection

router = APIRouter(prefix="/hotspots", tags=["WiFi"])

# --------------------------------------------------------------
# DISCOVERY ENDPOINTS (ALL PUBLIC)
# --------------------------------------------------------------

@router.get(
    "/",
    summary="List all WiFi hotspots",
    description=(
        "Returns the full list of enriched public WiFi hotspots, including core attributes, "
        "location coordinates, and any computed risk metadata.\n\n"
        "**Cyber Exposure Score Explanation**\n"
        "Each hotspot may include a *Cyber Exposure Score* — a simple 0–100 value indicating "
        "how risky the hotspot may be:\n\n"
        "🟢 **0–30: Low Risk (Safe)** — Strong security and low environmental threat.\n"
        "🟡 **31–60: Medium Risk (Caution)** — Some concerns such as weaker security, "
        "moderate crime levels, or minor user‑reported issues.\n"
        "🔴 **61–100: High Risk (Unsafe)** — Open network, high crime exposure, or suspicious "
        "incidents. Avoid for sensitive tasks.\n\n"
        "This helps users compare hotspots at a glance when viewing maps or lists."
    ),
    responses={200: {"description": "List of all hotspots (enriched view)"}}
)
async def list_hotspots(db: Connection = Depends(get_db)):
    rows = await db.fetch("""
        SELECT *,
               ST_Y(geom_geog::geometry) AS lat,
               ST_X(geom_geog::geometry) AS lon
        FROM api.api_wifi_hotspot_risk
        ORDER BY city NULLS LAST, name NULLS LAST;
    """)
    return [dict(r) for r in rows]


@router.get(
    "/search",
    summary="Search hotspots by name",
    description=(
        "Performs a case‑insensitive match on hotspot names. "
        "Useful when the user types an area name, building name, or partial SSID."
    )
)
async def search_by_name(
    name: str = Query(..., description="Partial hotspot name, e.g. `Civic`"),
    db: Connection = Depends(get_db)
):
    rows = await db.fetch("""
        SELECT *,
               ST_Y(geom_geog::geometry) AS lat,
               ST_X(geom_geog::geometry) AS lon
        FROM api.api_wifi_hotspot_risk
        WHERE name ILIKE '%' || $1 || '%'
        ORDER BY name;
    """, name)
    return [dict(r) for r in rows]


@router.get(
    "/postcode",
    summary="Find hotspots by postcode prefix",
    description="Filters hotspots whose postcode begins with the provided prefix."
)
async def search_by_postcode(
    postcode: str = Query(..., description="Postcode prefix, e.g. `LS1`"),
    db: Connection = Depends(get_db)
):
    rows = await db.fetch("""
        SELECT *,
               ST_Y(geom_geog::geometry) AS lat,
               ST_X(geom_geog::geometry) AS lon
        FROM api.api_wifi_hotspot_risk
        WHERE postcode ILIKE $1 || '%'
        ORDER BY postcode, name;
    """, postcode)
    return [dict(r) for r in rows]


@router.get(
    "/city",
    summary="List hotspots in a city",
    description="Returns hotspots for the specified city (case‑insensitive)."
)
async def search_by_city(
    city: str = Query(..., description="City name, e.g. `Leeds`"),
    db: Connection = Depends(get_db)
):
    rows = await db.fetch("""
        SELECT *,
               ST_Y(geom_geog::geometry) AS lat,
               ST_X(geom_geog::geometry) AS lon
        FROM api.api_wifi_hotspot_risk
        WHERE LOWER(city) = LOWER($1)
        ORDER BY name;
    """, city)
    return [dict(r) for r in rows]


# --------------------------------------------------------------
# NEAREST / NEAR (PUBLIC)
# --------------------------------------------------------------

@router.get("/nearest")
async def nearest(
    lat: float, lon: float, db: Connection = Depends(get_db)
):
    rows = await db.fetch("""
        WITH q AS (
            SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
        )
        SELECT h.*,
               ST_Y(h.geom_geog::geometry) AS lat,
               ST_X(h.geom_geog::geometry) AS lon,
               ST_Distance(h.geom_geog, q.g) AS dist
        FROM api.api_wifi_hotspot_risk h, q
        ORDER BY dist ASC
        LIMIT 1;
    """, lat, lon)
    return dict(rows[0]) if rows else {"message": "No hotspots found"}


@router.get("/nearest/knn")
async def nearest_knn(lat: float, lon: float, k: int = 5):
    rows = await models.get_hotspots_knn(lat, lon, k)
    return [dict(r) for r in rows]


@router.get("/near")
async def hotspots_near(
    lat: float, lon: float, radius: int = 500, db: Connection = Depends(get_db)
):
    rows = await db.fetch("""
        WITH q AS (
            SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
        )
        SELECT h.*,
               ST_Y(h.geom_geog::geometry) AS lat,
               ST_X(h.geom_geog::geometry) AS lon,
               ST_Distance(h.geom_geog, q.g) AS dist
        FROM api.api_wifi_hotspot_risk h, q
        WHERE ST_DWithin(h.geom_geog, q.g, $3)
        ORDER BY dist ASC;
    """, lat, lon, radius)
    return [dict(r) for r in rows]


# --------------------------------------------------------------
# ADMIN‑PROTECTED UPDATES
# --------------------------------------------------------------

@router.patch(
    "/{wifi_id}/status",
    summary="Update hotspot status",
    dependencies=[Depends(require_user)],
)
async def update_status(
    wifi_id: str,
    status: str = Query(..., description="New status, e.g. `Live`")
):
    await models.update_hotspot_status(wifi_id, status)
    return {"message": "Status updated"}


@router.patch(
    "/{wifi_id}/security",
    summary="Update hotspot security mode",
    dependencies=[Depends(require_user)],
)
async def update_security(
    wifi_id: str,
    security_protection: str = Query(..., description="One of: `open`, `wpa2`, `wpa3`")
):
    await models.update_hotspot_security(wifi_id, security_protection)
    return {"message": "Security updated"}


# --------------------------------------------------------------
# DETAILS (PUBLIC)
# --------------------------------------------------------------

@router.get(
    "/{wifi_id}",
    response_model=Hotspot,
    summary="Get hotspot details",
    description=(
        "Returns full hotspot details including:\n"
        "- Basic metadata\n"
        "- Security mode\n"
        "- Crime exposure\n"
        "- **Cyber Exposure Score** (0–100 risk indicator)\n"
        "- Latitude/Longitude\n"
    )
)
async def get_hotspot(
    wifi_id: str, db: Connection = Depends(get_db)
):
    key = f"hotspot:{wifi_id}"
    cached = await cache_get(key)
    if cached:
        return json.loads(cached)

    row = await db.fetchrow("""
        SELECT *,
               ST_Y(geom_geog::geometry) AS lat,
               ST_X(geom_geog::geometry) AS lon
        FROM api.api_wifi_hotspot_risk
        WHERE wifi_id = $1;
    """, wifi_id)

    if not row:
        raise HTTPException(404, "Hotspot not found")

    hotspot = dict(row)
    await cache_setex(key, 300, json.dumps(hotspot))
    return hotspot