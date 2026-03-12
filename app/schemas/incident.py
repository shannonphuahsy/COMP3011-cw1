from pydantic import BaseModel

class IncidentCreate(BaseModel):
    wifi_id: str
    bssid: str
    description: str