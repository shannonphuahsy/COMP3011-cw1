from fastapi import APIRouter, Query, Depends
from app.core.auth_combined import require_api_key_or_jwt
from app.db import models


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_api_key_or_jwt)]
)


@router.get(
    "/nearby",
    summary="Find hotspots near a point",
    description=(
        "Returns hotspots within **radius** meters of the given **lat/lon** using `ST_DWithin` "
        "on indexed geography for fast geospatial search. Sorted by distance (ascending)."
    ),
    responses={200: {"description": "List of nearby hotspots (possibly empty)"}, 422: {"description": "Validation error"}}
)
async def nearby(
    lat: float = Query(..., description="Latitude in WGS84 (e.g., 53.800)"),
    lon: float = Query(..., description="Longitude in WGS84 (e.g., -1.549)"),
    radius: int = Query(500, ge=1, le=5000, description="Search radius in meters (1–5000)")
):
    rows = await models.get_hotspots_near(lat, lon, radius)
    return [dict(r) for r in rows]


@router.get(
    "/ranked",
    summary="Top hotspots by exposure score (per city)",
    description="Returns the top **N** hotspots ordered by `cyber_exposure_score` (descending) for a given city.",
    responses={200: {"description": "Top hotspots by risk score"}, 422: {"description": "Validation error"}}
)
async def ranked(
    city: str = Query(..., description="City name, case‑insensitive (e.g., Leeds)"),
    limit: int = Query(10, ge=1, le=100, description="Max results (1–100)")
):
    rows = await models.get_ranked_hotspots(city, limit)
    return [dict(r) for r in rows]


@router.get(
    "/crime/{wifi_id}",
    summary="Crime count near hotspot (12 months, 500 m)",
    description="Reads the pre‑aggregated `crime_12m_count` from the materialized view for the specified `wifi_id`.",
    responses={200: {"description": "Crime count payload"}}
)
async def crime(wifi_id: str):
    count = await models.get_crime_count(wifi_id)
    return {"wifi_id": wifi_id, "crime_last_12m": count}