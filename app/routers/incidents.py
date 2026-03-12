from fastapi import APIRouter, HTTPException, status
from app.db import models
from app.schemas.incident import IncidentCreate, IncidentUpdate

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new safety incident",
    description=(
        "Adds a user‑reported safety incident attached to a hotspot/BSSID. "
        "This does not modify the authoritative hotspot dataset."
    ),
    responses={
        201: {"description": "Incident created"},
        422: {"description": "Validation error"}
    }
)
async def create_incident_route(payload: IncidentCreate):
    row = await models.create_incident(payload.wifi_id, payload.bssid, payload.description)
    return dict(row)


@router.get(
    "/{wifi_id}",
    summary="List incidents for a hotspot",
    description="Returns incidents associated with a **wifi_id**, ordered by newest first.",
    responses={200: {"description": "Array of incidents (possibly empty)"}}
)
async def list_for_wifi(wifi_id: str):
    rows = await models.list_incidents(wifi_id)
    return [dict(r) for r in rows]


@router.patch(
    "/{incident_id}",
    summary="Update an incident description",
    description="Updates the **description** of an existing incident.",
    responses={
        200: {"description": "Incident updated"},
        404: {"description": "Incident not found"},
        422: {"description": "Validation error"}
    }
)
async def update_incident_route(incident_id: int, body: IncidentUpdate):
    row = await models.update_incident(incident_id, body.description)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return dict(row)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    description="Deletes the specified incident. Returns **204 No Content** on success.",
    responses={
        204: {"description": "Incident deleted"},
        404: {"description": "Incident not found (if you choose to enforce)"},
    }
)
async def delete_incident_route(incident_id: int):
    await models.delete_incident(incident_id)
    return None
