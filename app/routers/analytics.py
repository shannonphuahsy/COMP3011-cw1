# app/routers/analytics.py

from fastapi import APIRouter, HTTPException, Query
from app.db import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get(
    "/ranked",
    summary="Top hotspots by exposure score (per city)",
    description="Returns the top **N** hotspots ordered by `cyber_exposure_score` (descending) for a given city.",
    responses={
        200: {"description": "Top hotspots by risk score"},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "city"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def ranked(
    city: str = Query(..., description="City name, case‑insensitive (e.g., Leeds)"),
    limit: int = Query(10, ge=1, le=100, description="Max results (1–100)"),
):
    rows = await models.get_ranked_hotspots(city, limit)
    return [dict(r) for r in rows]

@router.get(
    "/crime/{wifi_id}",
    summary="Crime count near hotspot (12 months, 500 m)",
    description="Returns the pre‑aggregated `crime_12m_count` for the specified hotspot.",
    responses={
        200: {"description": "Crime count payload"},
        404: {"description": "Hotspot not found"},
    },
)
async def crime(wifi_id: str):
    # Validate hotspot exists
    hotspot = await models.get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    # Fetch crime count
    count = await models.get_crime_count(wifi_id)

    return {"wifi_id": wifi_id, "crime_last_12m": count}