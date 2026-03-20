# app/services/scoring.py

from typing import Any, Dict, List, Optional
from app.schemas.assessment import SafetyAssessment, Reason, Recommendation

def compute_score(
    hotspot: Dict[str, Any],
    crime_count: int,
    bssid: str,
    recent_incidents: List[Dict[str, Any]],
    client_hints: Optional[Dict[str, bool]] = None,
    ssid: Optional[str] = None,
    distance: Optional[float] = None,
) -> SafetyAssessment:

    client_hints = client_hints or {}
    reasons: List[Reason] = []
    points: int = 0


    sec = (hotspot.get("security_protection") or "").lower()

    if sec == "open":
        reasons.append(Reason(
            code="OPEN_NETWORK",
            message="This network is unencrypted (Open). Public Wi‑Fi without encryption is vulnerable to sniffing and MAN‑IN‑THE‑MIDDLE attacks.",
            weight=40
        ))
        points += 40

    elif sec == "wpa2":
        reasons.append(Reason(
            code="WPA2_NETWORK",
            message="This network uses WPA2. Better than Open but vulnerable to known attacks and weak passwords.",
            weight=20
        ))
        points += 20

    elif sec == "wpa3":
        reasons.append(Reason(
            code="WPA3_NETWORK",
            message="This network uses WPA3 (SAE), providing stronger modern protections.",
            weight=5
        ))
        points += 5

    else:
        reasons.append(Reason(
            code="UNKNOWN_SECURITY",
            message="Security mode is unknown; uncertainty increases risk.",
            weight=15
        ))
        points += 15

    if recent_incidents:
        reasons.append(Reason(
            code="INCIDENT_HISTORY",
            message="Users have reported issues or suspicious behaviour at this hotspot.",
            weight=15
        ))
        points += 15

    if crime_count >= 20:
        reasons.append(Reason(
            code="HIGH_CRIME_AREA",
            message="This hotspot is in an area with high recent crime, increasing opportunistic threat risk.",
            weight=10
        ))
        points += 10
    elif crime_count >= 10:
        reasons.append(Reason(
            code="MODERATE_CRIME_AREA",
            message="This hotspot is in an area with moderate recent crime.",
            weight=5
        ))
        points += 5


    if ssid:
        s_lower = ssid.lower()
        common_spoof_targets = ["free", "public", "guest", "wifi", "airport", "hotel"]

        if any(p in s_lower for p in common_spoof_targets):
            reasons.append(Reason(
                code="GENERIC_SSID",
                message=f"The SSID '{ssid}' is very common and can be easily spoofed by rogue hotspots.",
                weight=10
            ))
            points += 10

    # --------------------------------------------------------
    # 5. Captive Portal / Status Heuristic
    # --------------------------------------------------------
    status = (hotspot.get("status") or "").lower()
    if status in ("planned", "suspended", "retired"):
        reasons.append(Reason(
            code="UNUSUAL_STATUS",
            message="This hotspot has a non-standard operational status, which can indicate an unreliable configuration.",
            weight=5
        ))
        points += 5

    if ssid and "login" in ssid.lower():
        reasons.append(Reason(
            code="CAPTIVE_PORTAL_PHISHING_RISK",
            message="The SSID name suggests a login/captive portal, which may be used for phishing.",
            weight=10
        ))
        points += 10

    if distance is not None:
        if distance > 30:
            reasons.append(Reason(
                code="DISTANCE_ANOMALY",
                message="The hotspot's mapped location is unusually far from the user's device.",
                weight=10
            ))
            points += 10

    if client_hints.get("vpn"):
        reasons.append(Reason(
            code="VPN_ACTIVE",
            message="VPN is active, reducing exposure to interception.",
            weight=-15
        ))
        points -= 15

    if client_hints.get("https_only"):
        reasons.append(Reason(
            code="HTTPS_ONLY",
            message="HTTPS-only browsing reduces data exposure on insecure networks.",
            weight=-10
        ))
        points -= 10

    score = max(0, min(100, points))

    if score >= 60:
        verdict = "unsafe"
    elif score >= 30:
        verdict = "caution"
    else:
        verdict = "safe"


    recommendations: List[Recommendation] = []

    if verdict == "unsafe":
        recommendations.append(Recommendation(
            message="Avoid logging into sensitive accounts or making payments."
        ))
        recommendations.append(Recommendation(
            message="Use mobile data or a trusted VPN if you must stay connected."
        ))
        if ssid and "free" in ssid.lower():
            recommendations.append(Recommendation(
                message="Be cautious of networks with very generic names—attackers often spoof them."
            ))

    elif verdict == "caution":
        recommendations.append(Recommendation(
            message="Use HTTPS-only sites and consider enabling a VPN."
        ))
        recommendations.append(Recommendation(
            message="Avoid entering personal details into captive portals."
        ))

    else:  # safe
        recommendations.append(Recommendation(
            message="Network appears suitable for general use."
        ))
        recommendations.append(Recommendation(
            message="Continue following good cyber hygiene, such as keeping devices updated."
        ))


    context = {
        "security_protection": sec,
        "crime_12m_count": crime_count,
        "incidents_count": len(recent_incidents),
        "distance_meters": distance,
        "status": hotspot.get("status"),
        "latitude": hotspot.get("latitude"),
        "longitude": hotspot.get("longitude"),
    }

    return SafetyAssessment(
        wifi_id=hotspot["wifi_id"],
        bssid=bssid,
        verdict=verdict,
        score=score,
        reasons=reasons,
        recommendations=recommendations,
        context=context,
    )