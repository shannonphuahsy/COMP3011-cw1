from pydantic import BaseModel, Field
from typing import Optional

class Hotspot(BaseModel):
    wifi_id: str = Field(..., description="Hotspot unique ID")
    name: Optional[str] = Field(None, description="Hotspot name/label")
    postcode: Optional[str] = Field(None, description="Postcode")
    city: Optional[str] = Field(None, description="City")
    latitude: float = Field(..., description="WGS84 latitude")
    longitude: float = Field(..., description="WGS84 longitude")
    status: Optional[str] = Field(None, description="Operational status")
    security_protection: Optional[str] = Field(None, description="open|wpa2|wpa3")
    cyber_exposure_score: Optional[float] = Field(None, description="Composite exposure score")

    class Config:
        json_schema_extra = {
            "example": {
                "wifi_id": "c297205e-1226-46de-9868-5103d098b1d9",
                "name": "Civic Hall Wi‑Fi",
                "postcode": "LS1 1UR",
                "city": "Leeds",
                "latitude": 53.799,
                "longitude": -1.549,
                "status": "Live",
                "security_protection": "wpa2",
                "cyber_exposure_score": 6.75
            }
        }