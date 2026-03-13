import pytest

@pytest.mark.asyncio
async def test_safety_assessment(async_client, mapped_bssid):
    r = await async_client.get("/assessments/safety", params={"bssid": mapped_bssid})
    assert r.status_code == 200
    body = r.json()
    assert body["bssid"] == mapped_bssid
    assert "wifi_id" in body
    assert "risk_score" in body
    assert "crime_last_12m" in body
    assert "security_rating" in body