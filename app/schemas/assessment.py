from pydantic import BaseModel, Field
from typing import List

class SafetyAssessment(BaseModel):
    bssid: str = Field(..., description="BSSID queried")
    wifi_id: str = Field(..., description="Resolved WiFi ID for the BSSID")
    risk_score: float = Field(..., description="Composite risk score (higher = riskier)")
    crime_last_12m: int = Field(..., description="Crimes within 500 m over the last 12 months")
    security_rating: str = Field(..., description="Wi‑Fi security mode (open|wpa2|wpa3)")
    device_density: float = Field(..., description="Estimated devices per km² in the LSOA")
    risk_factors: List[str] = Field(..., description="Explanations driving the score")
    recommendations: List[str] = Field(..., description="Actionable safety advice")

    class Config:
        json_schema_extra = {
            "example": {
                "bssid": "AA:BB:CC:DD:EE:01",
                "wifi_id": "c297205e-1226-46de-9868-5103d098b1d9",
                "risk_score": 7.4,
                "crime_last_12m": 14,
                "security_rating": "open",
                "device_density": 1480.0,
                "risk_factors": [
                    "Open Wi‑Fi (no encryption)",
                    "Higher‑than‑average crime density",
                    "High device density — more potential attackers"
                ],
                "recommendations": [
                    "Avoid sensitive logins",
                    "Use a VPN",
                    "Disable file sharing and auto-connect",
                    "Ensure firewall is active"
                ]
            }
        }