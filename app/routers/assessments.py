# app/routers/assessments.py

from fastapi import APIRouter, HTTPException, Query, Request
from app.db import models
from app.services.scoring import compute_score
from app.schemas.assessment import SafetyAssessment
from app.core.limiter import limiter
from fastapi import Depends
from app.core.auth_combined import require_api_key_or_jwt

router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"],
    dependencies=[Depends(require_api_key_or_jwt)]  # read endpoints accept either auth
)


# ============================================================
# Helper: Resolve hotspot by SSID + location
# ============================================================
async def resolve_hotspot(ssid: str, lat: float, lon: float):
    row = await models.get_nearest_hotspot_by_ssid(lat=lat, lon=lon, ssid=ssid)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Insufficient information for this network"
        )
    return dict(row)


# ============================================================
# 1. SECURITY ASSESSMENT
# ============================================================
@router.get(
    "/security",
    summary="Security posture assessment (Open/WPA2/WPA3)",
)
@limiter.limit("30/minute")
async def security_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
    hotspot = await resolve_hotspot(ssid, lat, lon)
    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "security_protection": hotspot["security_protection"]
    }


# ============================================================
# 2. CRIME ASSESSMENT
# ============================================================
@router.get(
    "/crime",
    summary="Environmental crime risk assessment",
)
@limiter.limit("30/minute")
async def crime_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
    hotspot = await resolve_hotspot(ssid, lat, lon)
    crime = await models.get_crime_count(hotspot["wifi_id"])
    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "crime_12m_count": crime
    }


# ============================================================
# 3. INCIDENTS ASSESSMENT
# ============================================================
@router.get(
    "/incidents",
    summary="User-reported incident assessment",
)
@limiter.limit("30/minute")
async def incidents_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
    hotspot = await resolve_hotspot(ssid, lat, lon)
    incidents = await models.list_incidents(hotspot["wifi_id"])
    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "incidents": [dict(i) for i in incidents]
    }


# ============================================================
# 4. SSID SPOOFING RISK
# ============================================================
@router.get(
    "/ssid_risk",
    summary="SSID spoofing likelihood assessment",
)
@limiter.limit("30/minute")
async def ssid_risk_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
    hotspot = await resolve_hotspot(ssid, lat, lon)

    common_patterns = ["free", "public", "guest", "wifi", "airport", "hotel"]
    s_lower = ssid.lower()
    spoofable = any(p in s_lower for p in common_patterns)

    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "spoof_risk": "high" if spoofable else "normal"
    }


# ============================================================
# 5. ENVIRONMENT / STATUS / DISTANCE
# ============================================================
@router.get(
    "/environment",
    summary="Environmental & captive portal risk assessment",
)
@limiter.limit("30/minute")
async def environment_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...)
):
    row = await models.get_nearest_hotspot_by_ssid(lat, lon, ssid)
    if not row:
        raise HTTPException(404, "Insufficient information for this network")

    hotspot = dict(row)
    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "status": hotspot["status"],
        "distance_meters": hotspot.get("dist")
    }


# ============================================================
# 6. GENERAL SAFETY ASSESSMENT (COMBINED)
# ============================================================
@router.get(
    "/safety",
    response_model=SafetyAssessment,
    summary="General Wi‑Fi Safety Assessment",
    description=(
        "Combines all assessments: security posture, crime risk, user incidents, "
        "SSID spoofing likelihood, captive portal heuristics, distance anomalies, and "
        "client mitigations (VPN/HTTPS). Returns a final verdict and score."
    ),
)
@limiter.limit("30/minute")
async def general_safety_assessment(
    request: Request,
    ssid: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    vpn: bool = Query(False),
    https_only: bool = Query(False),
):
    row = await models.get_nearest_hotspot_by_ssid(lat=lat, lon=lon, ssid=ssid)
    if not row:
        raise HTTPException(404, "Insufficient information for this network")

    hotspot = dict(row)
    wifi_id = hotspot["wifi_id"]

    crime = await models.get_crime_count(wifi_id)
    incidents = await models.list_incidents(wifi_id)

    assessment = compute_score(
        hotspot=hotspot,
        crime_count=crime,
        bssid=hotspot.get("bssid") or "unknown",
        recent_incidents=incidents or [],
        evil_twin_suspected=False,
        client_hints={"vpn": vpn, "https_only": https_only},
        ssid=ssid,
        distance=hotspot.get("dist")
    )

    assessment.context["resolution_method"] = "ssid+location"
    assessment.context["confidence"] = "medium"
    assessment.context["note"] = (
        "Assessment based on SSID and location. "
        "SSID‑only identification is user-friendly but may be ambiguous."
    )

    return assessment