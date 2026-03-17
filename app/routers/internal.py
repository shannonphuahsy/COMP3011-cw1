# app/routers/internal.py

from fastapi import APIRouter, Depends, HTTPException
from app.services.api_key import require_api_key
from app.db.database import get_db
import time

router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)

START_TIME = time.time()

# --------------------------------------------------------------
# 1. SYSTEM STATISTICS
# --------------------------------------------------------------
@router.get("/stats", dependencies=[Depends(require_api_key)])
async def internal_stats():
    """
    Returns operational statistics for monitoring and debugging.
    """
    db = await get_db()

    hotspot_count = await db.fetchval("SELECT COUNT(*) FROM core.core_wifi_hotspot;")
    incident_count = await db.fetchval("SELECT COUNT(*) FROM api.api_user_incidents;")
    crime_count = await db.fetchval("SELECT COUNT(*) FROM core.core_crime;")

    uptime = int(time.time() - START_TIME)

    await db.close()

    return {
        "ok": True,
        "database": "connected",
        "hotspots": hotspot_count,
        "incidents": incident_count,
        "crime_records": crime_count,
        "uptime_seconds": uptime,
    }

# --------------------------------------------------------------
# 2. VERSION INFO
# --------------------------------------------------------------
@router.get("/version", dependencies=[Depends(require_api_key)])
async def version_info():
    """
    Returns database, PostGIS, and API version information.
    """
    db = await get_db()
    try:
        postgres_version = await db.fetchval("SELECT version();")
        postgis_version = await db.fetchval("SELECT PostGIS_Full_Version();")
    finally:
        await db.close()

    return {
        "api_version": "1.0.0",
        "postgres_version": postgres_version,
        "postgis_version": postgis_version,
    }