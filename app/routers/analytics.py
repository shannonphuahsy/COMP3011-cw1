from fastapi import APIRouter
from app.db import models

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/nearby")
async def nearby(lat: float, lon: float, radius: int = 500):
    rows = await models.get_hotspots_near(lat, lon, radius)
    return [dict(r) for r in rows]


@router.get("/ranked")
async def ranked(city: str, limit: int = 10):
    rows = await models.get_ranked_hotspots(city, limit)
    return [dict(r) for r in rows]


@router.get("/crime/{wifi_id}")
async def crime(wifi_id: str):
    count = await models.get_crime_count(wifi_id)
    return {"wifi_id": wifi_id, "crime_last_12m": count}