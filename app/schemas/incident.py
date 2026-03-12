from pydantic import BaseModel, Field

class IncidentCreate(BaseModel):
    wifi_id: str = Field(..., description="The hotspot's unique WiFi ID")
    bssid: str = Field(..., description="Access Point MAC/BSSID that observed the incident")
    description: str = Field(..., min_length=3, description="Short description of the incident")

    class Config:
        json_schema_extra = {
            "example": {
                "wifi_id": "c297205e-1226-46de-9868-5103d098b1d9",
                "bssid": "AA:BB:CC:DD:EE:01",
                "description": "Phishing captive portal observed near the venue"
            }
        }

class IncidentUpdate(BaseModel):
    description: str = Field(..., min_length=3, description="New description for the incident")

    class Config:
        json_schema_extra = {
            "example": {"description": "False alarm: maintenance landing page"}
        }