# app/routers/wifi_networks.py

from fastapi import APIRouter, HTTPException, Query
from app.db import models
from app.db.database import get_db
from app.schemas.hotspot import Hotspot
from app.cache import cache_get, cache_setex
import json

router = APIRouter(prefix="/hotspots", tags=["WiFi"])


# --------------------------------------------------------------
# DISCOVERY ENDPOINTS
# --------------------------------------------------------------

@router.get(
    "/",
    summary="List all WiFi hotspots",
    description=(
        "Returns the full list of enriched public WiFi hotspots, including core attributes "
        "and computed risk metadata. Useful for map visualisation, bulk browsing, or populating "
        "client-side hotspot lists."
    ),
    responses={
        200: {"description": "List of all hotspots (enriched view)"},
    }
)
async def list_hotspots():
    db = await get_db()
    try:
        rows = await db.fetch("""
            SELECT * 
            FROM api.api_wifi_hotspot_risk
            ORDER BY city NULLS LAST, name NULLS LAST;
        """)
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.get(
    "/search",
    summary="Search hotspots by name",
    description=(
        "Performs a case-insensitive partial match search on hotspot names. "
        "Useful for keyword-based discovery when the user types an area name, building name, "
        "or partial SSID."
    ),
    responses={200: {"description": "Matching hotspot results"}}
)
async def search_by_name(
    name: str = Query(..., description="Partial match on hotspot name, e.g. `Civic`")
):
    db = await get_db()
    try:
        rows = await db.fetch("""
            SELECT *
            FROM api.api_wifi_hotspot_risk
            WHERE name ILIKE '%' || $1 || '%'
            ORDER BY name;
        """, name)
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.get(
    "/postcode",
    summary="Find hotspots by postcode prefix",
    description=(
        "Returns hotspots whose `postcode` begins with the given prefix. Useful when the app "
        "knows a postcode (e.g., from user entry or device geolocation metadata)."
    ),
    responses={200: {"description": "Hotspots in the specified postcode prefix"}}
)
async def search_by_postcode(
    postcode: str = Query(..., description="Postcode prefix, e.g. `LS1`")
):
    db = await get_db()
    try:
        rows = await db.fetch("""
            SELECT *
            FROM api.api_wifi_hotspot_risk
            WHERE postcode ILIKE $1 || '%'
            ORDER BY postcode, name;
        """, postcode)
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.get(
    "/city",
    summary="List hotspots in a city",
    description=(
        "Fetches hotspots in the specified **city** (case-insensitive)."
        "Useful for city-wide filtering or populating local maps."
    ),
    responses={200: {"description": "Hotspots belonging to the specified city"}}
)
async def search_by_city(
    city: str = Query(..., description="Exact city name, e.g. `Leeds`")
):
    db = await get_db()
    try:
        rows = await db.fetch("""
            SELECT *
            FROM api.api_wifi_hotspot_risk
            WHERE LOWER(city) = LOWER($1)
            ORDER BY name;
        """, city)
        return [dict(r) for r in rows]
    finally:
        await db.close()


# --------------------------------------------------------------
# NEAREST (Single nearest point)
# --------------------------------------------------------------

@router.get(
    "/nearest",
    summary="Find the closest hotspot",
    description=(
        "Performs a proximity search to return **the single nearest hotspot** "
        "to the provided latitude and longitude. Uses PostGIS `ST_Distance` on an indexed "
        "`geography` column for efficient spatial lookup."
    ),
    responses={
        200: {"description": "The closest hotspot to the coordinates"},
        422: {"description": "Invalid latitude/longitude"},
    }
)
async def nearest(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lon: float = Query(..., description="Longitude (WGS84)")
):
    db = await get_db()
    try:
        rows = await db.fetch("""
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography AS g
            )
            SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
            FROM api.api_wifi_hotspot_risk h, q
            ORDER BY dist ASC
            LIMIT 1;
        """, lat, lon)

        return dict(rows[0]) if rows else {"message": "No hotspots found"}
    finally:
        await db.close()


# --------------------------------------------------------------
# NEAREST (K-NEAREST NEIGHBOURS — KNN)
# --------------------------------------------------------------

@router.get(
    "/nearest/knn",
    summary="Find the K nearest hotspots (KNN search)",
    description=(
        "Returns the **K closest hotspots** to the given coordinates using a "
        "PostGIS K‑Nearest Neighbour (KNN) index‑assisted query via the `<->` distance operator. "
        "This is significantly faster than computing distance for all hotspots, provided a GiST "
        "index exists on `geom_geog`."
    ),
    responses={200: {"description": "Array of the K closest hotspots"}}
)
async def nearest_knn(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lon: float = Query(..., description="Longitude (WGS84)"),
    k: int = Query(5, ge=1, le=50, description="Number of nearest hotspots to return")
):
    rows = await models.get_hotspots_knn(lat, lon, k)
    return [dict(r) for r in rows]


# --------------------------------------------------------------
# RADIUS SEARCH
# --------------------------------------------------------------

@router.get(
    "/near",
    summary="Find hotspots within a radius",
    description=(
        "Returns all hotspots located within **N metres** of the provided coordinate. "
        "Uses `ST_DWithin`, which is efficient on a `geography` column with a GiST index. "
        "Ideal for 'hotspots near me' views."
    ),
    responses={200: {"description": "Hotspots within the specified radius"}}
)
async def hotspots_near(
    lat: float = Query(..., description="Latitude (WGS84)"),
    lon: float = Query(..., description="Longitude (WGS84)"),
    radius: int = Query(500, ge=1, le=5000, description="Search radius in metres")
):
    db = await get_db()
    try:
        rows = await db.fetch("""
            WITH q AS (
                SELECT ST_SetSRID(ST_MakePoint($2,$1), 4326)::geography AS g
            )
            SELECT h.*, ST_Distance(h.geom_geog, q.g) AS dist
            FROM api.api_wifi_hotspot_risk h, q
            WHERE ST_DWithin(h.geom_geog, q.g, $3)
            ORDER BY dist ASC;
        """, lat, lon, radius)
        return [dict(r) for r in rows]
    finally:
        await db.close()


# --------------------------------------------------------------
# PARTIAL UPDATES
# --------------------------------------------------------------

@router.patch(
    "/{wifi_id}/status",
    summary="Update hotspot status",
    description=(
        "Updates the public‑facing operational **status** of a hotspot "
        "(e.g. `Live`, `Planned`, `Suspended`). This modifies project metadata but does not "
        "alter risk scores or geography."
    ),
    responses={200: {"description": "Status updated"}}
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
    description=(
        "Updates the **security_protection** mode for a hotspot "
        "(e.g. `open`, `wpa2`, `wpa3`). Used for correcting metadata or reflecting changes "
        "from local authorities/operators."
    ),
    responses={200: {"description": "Security mode updated"}}
)
async def update_security(
    wifi_id: str,
    security_protection: str = Query(..., description="One of: `open`, `wpa2`, `wpa3`")
):
    await models.update_hotspot_security(wifi_id, security_protection)
    return {"message": "Security updated"}


# --------------------------------------------------------------
# DETAILS (CACHED) — MUST BE LAST
# --------------------------------------------------------------

@router.get(
    "/{wifi_id}",
    response_model=Hotspot,
    summary="Get hotspot details",
    description=(
        "Returns the **complete enriched hotspot record**, including core metadata, "
        "location, risk context, and computed fields. This endpoint uses a 5‑minute Redis cache "
        "to reduce latency and database load."
    ),
    responses={
        200: {"description": "Full hotspot details"},
        404: {"description": "Hotspot not found"}
    }
)
async def get_hotspot(wifi_id: str):
    key = f"hotspot:{wifi_id}"
    cached = await cache_get(key)

    if cached:
        return json.loads(cached)

    row = await models.get_hotspot_by_wifi_id(wifi_id)

    if not row:
        raise HTTPException(404, "Hotspot not found")

    await cache_setex(key, 300, json.dumps(dict(row)))
    return dict(row)