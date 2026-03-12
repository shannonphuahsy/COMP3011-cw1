from app.schemas.assessment import SafetyAssessment


def compute_score(hotspot, crime_count, bssid):

    score = 0
    risk_factors = []
    recs = []

    # 1. Crime
    crime_factor = min(crime_count / 5, 5)
    score += crime_factor
    if crime_factor > 2:
        risk_factors.append("High crime density around hotspot")

    # 2. Security
    security = hotspot["security_protection"]
    if security == "open":
        score += 3
        risk_factors.append("Open WiFi network (no encryption)")
        recs.append("Avoid sensitive logins. Use a VPN.")
    elif security == "wpa2":
        score += 1
    elif security == "wpa3":
        score += 0.5

    # 3. Device density
    dd = hotspot["device_density_per_km2"] or 0
    dd_factor = min(dd / 1000, 3)
    score += dd_factor
    if dd_factor > 1:
        risk_factors.append("High device density — more potential attackers")

    # 4. Compose recommendations
    recs.append("Ensure firewall is active")
    recs.append("Disable file sharing and auto-connect")

    return SafetyAssessment(
        bssid=bssid,
        wifi_id=hotspot["wifi_id"],
        risk_score=round(score, 2),
        crime_last_12m=crime_count,
        security_rating=security,
        device_density=dd,
        risk_factors=risk_factors,
        recommendations=recs
    )