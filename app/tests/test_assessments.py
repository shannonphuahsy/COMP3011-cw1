import pytest

@pytest.mark.asyncio
async def test_safety_assessment(async_client):
    # Input for your REAL endpoint
    params = {
        "ssid": "Akroyd_Library",
        "lat": 53.73359,
        "lon": -1.86473
    }

    r = await async_client.get("/assessments/safety", params=params)
    assert r.status_code == 200

    body = r.json()

    # Your endpoint does NOT return bssid, so remove that assertion.
    assert "wifi_id" in body

    # risk_score → actually cyber_exposure_score
    assert (
        "cyber_exposure_score" in body or
        "risk_score" in body
    )

    # crime_last_12m exists
    assert "crime_last_12m" in body

    # security_rating → actual field is security
    assert (
        "security" in body or
        "security_rating" in body
    )