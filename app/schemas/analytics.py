from pydantic import BaseModel

class NearbyHotspot(BaseModel):
    wifi_id: str
    dist: float
    cyber_exposure_score: float