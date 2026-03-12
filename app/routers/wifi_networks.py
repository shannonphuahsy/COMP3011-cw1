from fastapi import APIRouter, HTTPException
from app.db import models
from app.schemas.hotspot import Hotspot

router = APIRouter(prefix="/hotspots", tags=["Hotspots"])


@router.get("/{wifi_id}", response_model=Hotspot)
async def get_hotspot(wifi_id: str):
    row = await models.get_hotspot_by_wifi_id(wifi_id)
    if not row:
        raise HTTPException(404, "Hotspot not found")
    return dict(row)


@router.patch("/{wifi_id}/status")
async def update_status(wifi_id: str, status: str):
    await models.update_hotspot_status(wifi_id, status)
    return {"message": "Status updated"}


@router.patch("/{wifi_id}/security")
async def update_security(wifi_id: str, security_protection: str):
    await models.update_hotspot_security(wifi_id, security_protection)
    return {"message": "Security level updated"}