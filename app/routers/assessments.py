from fastapi import APIRouter, HTTPException
from app.db import models
from app.services.scoring import compute_score
from app.schemas.assessment import SafetyAssessment

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/safety", response_model=SafetyAssessment)
async def safety(bssid: str):
    wifi_id = await models.get_wifi_id_from_bssid(bssid)
    if not wifi_id:
        raise HTTPException(404, "BSSID not mapped to any hotspot")

    hotspot = await models.get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        raise HTTPException(404, "Hotspot not found")

    crime_count = await models.get_crime_count(wifi_id)

    safety = compute_score(hotspot, crime_count, bssid)

    return safety