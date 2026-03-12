from pydantic import BaseModel
from typing import Optional

class Hotspot(BaseModel):
    wifi_id: str
    name: Optional[str]
    address: Optional[str]
    postcode: Optional[str]
    city: Optional[str]
    latitude: float
    longitude: float
    status: Optional[str]
    security_protection: Optional[str]
    cyber_exposure_score: Optional[float]