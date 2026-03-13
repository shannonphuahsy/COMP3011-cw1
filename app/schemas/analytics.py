from pydantic import BaseModel, ConfigDict

class NearbyHotspot(BaseModel):
    wifi_id: str
    dist: float
    cyber_exposure_score: float
    model_config = ConfigDict(from_attributes=True)