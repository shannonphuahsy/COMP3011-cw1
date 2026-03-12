from pydantic import BaseModel
from typing import List

class SafetyAssessment(BaseModel):
    bssid: str
    wifi_id: str
    risk_score: float
    crime_last_12m: int
    security_rating: str
    device_density: float
    risk_factors: List[str]
    recommendations: List[str]