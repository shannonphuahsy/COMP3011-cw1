from fastapi import APIRouter, HTTPException, Query
from app.db import models
from app.services.scoring import compute_score
from app.schemas.assessment import SafetyAssessment

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.get(
    "/safety",
    response_model=SafetyAssessment,
    summary="Safety assessment when a user connects",
    description=(
        "Given an Access Point **BSSID**, resolves the hotspot (`wifi_id`), fetches crime and context, and returns "
        "a **composite safety assessment** with risk score, driving factors, and practical recommendations."
    ),
    responses={
        200: {"description": "Safety assessment"},
        404: {"description": "BSSID not mapped or hotspot not found"},
        422: {"description": "Validation error"}
    }
)
async def safety(
    bssid: str = Query(..., description="Access Point BSSID (MAC), e.g. `AA:BB:CC:DD:EE:01`")
):
    wifi_id = await models.get_wifi_id_from_bssid(bssid)
    if not wifi_id:
        raise HTTPException(status_code=404, detail="BSSID not mapped to any hotspot")

    hotspot = await models.get_hotspot_by_wifi_id(wifi_id)
    if not hotspot:
        raise HTTPException(status_code=404, detail="Hotspot not found")

    crime_count = await models.get_crime_count(wifi_id)
    return compute_score(hotspot, crime_count, bssid)