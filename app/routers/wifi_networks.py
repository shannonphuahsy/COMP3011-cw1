from fastapi import APIRouter, HTTPException, Query
from app.db import models
from app.schemas.hotspot import Hotspot

router = APIRouter(prefix="/hotspots", tags=["WiFi"])

@router.get(
    "/{wifi_id}",
    response_model=Hotspot,
    summary="Get hotspot details",
    description=(
        "Returns the **enriched hotspot** record (with risk fields) for the given `wifi_id`.\n"
        "Data originates from authoritative public sources; enrichment comes from internal views."
    ),
    responses={404: {"description": "Hotspot not found"}}
)
async def get_hotspot(wifi_id: str):
    row = await models.get_hotspot_by_wifi_id(wifi_id)
    if not row:
        raise HTTPException(status_code=404, detail="Hotspot not found")
    return dict(row)


@router.patch(
    "/{wifi_id}/status",
    summary="Update hotspot status",
    description="Sets the hotspot **status** (e.g., Planned, Live, Suspended, Retired).",
    responses={200: {"description": "Status updated"}, 422: {"description": "Missing or invalid status"}}
)
async def update_status(
    wifi_id: str,
    status: str = Query(..., description="New status, e.g. `Live`")
):
    await models.update_hotspot_status(wifi_id, status)
    return {"message": "Status updated"}


@router.patch(
    "/{wifi_id}/security",
    summary="Update hotspot security mode",
    description="Sets the hotspot **security_protection** (e.g., `open|wpa2|wpa3`).",
    responses={200: {"description": "Security mode updated"}, 422: {"description": "Missing/invalid value"}}
)
async def update_security(
    wifi_id: str,
    security_protection: str = Query(..., description="One of: `open|wpa2|wpa3`")
):
    await models.update_hotspot_security(wifi_id, security_protection)
    return {"message": "Security level updated"}
