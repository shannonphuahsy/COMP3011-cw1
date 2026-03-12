from fastapi import APIRouter
from app.db import models
from app.schemas.incident import IncidentCreate

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/")
async def create(data: IncidentCreate):
    row = await models.create_incident(data.wifi_id, data.bssid, data.description)
    return dict(row)


@router.get("/{wifi_id}")
async def list_for_wifi(wifi_id: str):
    rows = await models.list_incidents(wifi_id)
    return [dict(r) for r in rows]


@router.delete("/{incident_id}")
async def delete(incident_id: int):
    await models.delete_incident(incident_id)
    return {"message": "Incident deleted"}