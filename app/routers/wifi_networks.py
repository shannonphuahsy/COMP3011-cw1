# app/routers/wifi_networks.py

from fastapi import APIRouter, HTTPException, Query, Depends
from app.db import models
from app.db.database import get_db
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
    description="Returns hotspots whose name matches the provided search term."
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
    "/city",
    summary="List hotspots in a city",
    description="Returns all WiFi hotspots that match the given city name."
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

@router.get(
    "/nearest",
    summary="Find nearest hotspot",
    description="Returns the closest WiFi hotspot to the given coordinates. Latitude and Longitude coordinates can be found from the previous endpoints."
)
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


@router.get(
    "/nearest/knn",
    summary="Find K nearest hotspots",
    description="Returns the K nearest WiFi hotspots ordered by distance."
)
async def nearest_knn(lat: float, lon: float, k: int = 5):
    rows = await models.get_hotspots_knn(lat, lon, k)
    return [dict(r) for r in rows]


@router.get(
    "/near",
    summary="Find hotspots within radius",
    description="Returns all WiFi hotspots within the specified radius (meters)."
)
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
    description="Updates the operational status of a WiFi hotspot (admin‑only).",
    dependencies=[Depends(require_user)],
)
async def update_status(
    wifi_id: str,
    status: str = Query(..., description="New status, e.g. `Live`")
):
    # Validate hotspot exists
    hotspot = await models.get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    await models.update_hotspot_status(wifi_id, status)
    return {"message": "Status updated"}


@router.patch(
    "/{wifi_id}/security",
    summary="Update hotspot security mode",
    description="Updates the security mode of a WiFi hotspot (admin‑only).",
    dependencies=[Depends(require_user)],
)
async def update_security(
    wifi_id: str,
    security_protection: str = Query(..., description="One of: `open`, `wpa2`, `wpa3`")
):
    # Validate hotspot exists
    hotspot = await models.get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    await models.update_hotspot_security(wifi_id, security_protection)
    return {"message": "Security updated"}

