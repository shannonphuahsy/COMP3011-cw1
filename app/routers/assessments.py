# app/routers/assessments.py

from fastapi import APIRouter, HTTPException, Query, Request
from app.db import models
from app.services.scoring import compute_score
from app.schemas.assessment import SafetyAssessment, Reason, Recommendation
from app.core.limiter import limiter

router = APIRouter(prefix="/assessments", tags=["Assessments"])


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
    description=(
        "Returns the security mode of the identified hotspot "
        "(e.g., Open, WPA2, WPA3). This helps users understand "
        "the basic technical protection used by the network."
    ),
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
    description=(
        "Shows the number of recorded crime incidents within the "
        "hotspot's geospatial catchment area. Higher counts may indicate "
        "a riskier physical environment."
    ),
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
    summary="User‑reported incident assessment",
    description=(
        "Lists recent user‑reported cybersecurity or suspicious activity "
        "incidents associated with this hotspot. Reports may include phishing "
        "attempts, fake captive portals or strange network behaviour."
    ),
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
    description=(
        "Estimates whether the network name (SSID) is commonly used by "
        "malicious actors — for example names like 'Free WiFi', 'Airport‑WiFi', "
        "'Guest', or similar generic labels that are often spoofed."
    ),
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
    spoofable = any(p in ssid.lower() for p in common_patterns)

    return {
        "ssid": ssid,
        "wifi_id": hotspot["wifi_id"],
        "spoof_risk": "high" if spoofable else "normal"
    }


# ============================================================
# 5. ENVIRONMENT ASSESSMENT
# ============================================================
@router.get(
    "/environment",
    summary="Environmental and captive‑portal risk assessment",
    description=(
        "Provides contextual information about the hotspot environment, "
        "including its operational status and distance from the provided "
        "location. Useful for distinguishing legitimate infrastructure "
        "from fake or suspicious networks."
    ),
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
@router.get(
    "/safety",
    summary="General Wi‑Fi Safety Assessment",
    description=(
        "Returns a complete Wi‑Fi safety verdict based on SSID + location, using the "
        "**cyber_exposure_score stored in the database**. Combines security, crime, SSID risk, "
        "environmental factors and final recommendations.\n\n"
        "**🟢 0–30: Low Risk** — Strong security, low crime, no suspicious activity.\n"
        "**🟡 31–60: Medium Risk** — Some concerns such as weaker security or minor incidents.\n"
        "**🔴 61–100: High Risk** — Open networks, suspicious incidents, high crime areas.\n"
    ),
    responses={200: {"description": "Composite safety assessment"}}
)
@limiter.limit("30/minute")
async def safety_assessment(
    request: Request,
    ssid: str = Query(..., description="SSID of the Wi‑Fi network"),
    lat: float = Query(..., description="Latitude of the device"),
    lon: float = Query(..., description="Longitude of the device"),
):
    # --------------------------------------------------
    # 1. Resolve hotspot from SSID + location
    # --------------------------------------------------
    hotspot = await resolve_hotspot(ssid, lat, lon)
    wifi_id = hotspot["wifi_id"]

    # --------------------------------------------------
    # 2. Load DB‑stored cyber_exposure_score
    # --------------------------------------------------
    stored_row = await models.get_hotspot_by_wifi_id(wifi_id)
    if not stored_row:
        raise HTTPException(404, "Hotspot not found")

    cyber_score = stored_row.get("cyber_exposure_score", 0)

    # --------------------------------------------------
    # 3. Load other signals
    # --------------------------------------------------
    crime_count = stored_row.get("crime_12m_count", 0)
    security = stored_row.get("security_protection", "unknown")
    distance = hotspot.get("dist")

    # SSID spoofing heuristic
    spoofable = any(
        p in ssid.lower()
        for p in ["free", "public", "guest", "wifi", "airport", "hotel"]
    )
    ssid_risk = "high" if spoofable else "normal"

    environment = {
        "status": stored_row.get("status"),
        "distance_meters": distance
    }

    # Incidents
    incidents = await models.list_incidents(wifi_id)
    incident_count = len(incidents)

    # --------------------------------------------------
    # 4. Verdict from stored score
    # --------------------------------------------------
    if cyber_score >= 60:
        verdict = "unsafe"
    elif cyber_score >= 30:
        verdict = "caution"
    else:
        verdict = "safe"

    # --------------------------------------------------
    # 5. Generate reasons based on contributing factors
    # --------------------------------------------------
    reasons = []

    # Security
    if security == "open":
        reasons.append({"code": "OPEN_NETWORK", "message": "This network is unencrypted.", "weight": 40})
    elif security == "wpa2":
        reasons.append({"code": "WPA2_NETWORK", "message": "WPA2 provides moderate security.", "weight": 20})
    elif security == "wpa3":
        reasons.append({"code": "WPA3_NETWORK", "message": "WPA3 provides strong security.", "weight": 5})

    # Crime
    if crime_count >= 20:
        reasons.append({"code": "HIGH_CRIME_AREA", "message": "High recent crime around this hotspot.", "weight": 10})
    elif crime_count >= 10:
        reasons.append({"code": "MODERATE_CRIME_AREA", "message": "Moderate recent crime around this hotspot.", "weight": 5})

    # Incidents
    if incident_count > 0:
        reasons.append({"code": "INCIDENT_HISTORY", "message": "Users have reported suspicious activity.", "weight": 10})

    # SSID spoof risk
    if ssid_risk == "high":
        reasons.append({"code": "GENERIC_SSID", "message": "SSID is common and easy to spoof.", "weight": 10})

    # --------------------------------------------------
    # 6. Recommendations based on verdict
    # --------------------------------------------------
    recommendations = []

    if verdict == "unsafe":
        recommendations.append({"message": "Avoid sensitive transactions on this network."})
        recommendations.append({"message": "Use a VPN or mobile data instead."})
    elif verdict == "caution":
        recommendations.append({"message": "Use HTTPS sites and consider a VPN."})
    else:
        recommendations.append({"message": "Network appears suitable for general use."})

    # --------------------------------------------------
    # 7. Final response
    # --------------------------------------------------
    return {
        "wifi_id": wifi_id,
        "ssid": ssid,

        # MAIN stored score
        "cyber_exposure_score": float(cyber_score),
        "verdict": verdict,

        # summarized sub-assessments
        "security": security,
        "crime_last_12m": crime_count,
        "incident_count": incident_count,
        "ssid_risk": ssid_risk,
        "environment": environment,

        # generated reasoning
        "reasons": reasons,
        "recommendations": recommendations,

        # raw DB + derived context
        "context": {
            "resolution_method": "ssid+location",
            "crime_12m_count": crime_count,
            "security_protection": security,
            "incidents_count": incident_count,
            "distance_meters": distance,
            "confidence": "high"
        }
    }