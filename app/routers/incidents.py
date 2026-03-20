# app/routers/incidents.py

from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from app.db import models
from app.core.limiter import limiter  # unified SlowAPI limiter
from app.services.dependencies import require_user  # ← ADDED

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new safety incident",
    description=(
        "Creates a **user-reported safety incident**, associated with a specific hotspot "
        "via its `wifi_id` and `bssid`. Incidents typically represent suspicious behaviour, "
        "device anomalies, or user-reported concerns. This endpoint **does not modify** any "
        "authoritative hotspot metadata, but contributes to user-facing risk intelligence."
    ),
    responses={
        201: {"description": "Incident successfully created"},
        422: {"description": "Validation error (missing or invalid fields)"}
    }
)
@limiter.limit("10/minute")
async def create_incident_route(
    request: Request,
    wifi_id: str = Query(..., description="The hotspot WiFi ID"),
    bssid: str = Query(..., description="MAC/BSSID involved in incident"),
    description: str = Query(..., min_length=3, description="Short description of the incident"),
    user=Depends(require_user)  # ← ADDED
):
    row = await models.create_incident(
        wifi_id,
        bssid,
        description
    )
    return dict(row)


@router.get(
    "/{wifi_id}",
    summary="List incidents for a hotspot",
    description=(
        "Returns all incidents associated with a given **WiFi hotspot ID (`wifi_id`)**, "
        "ordered by newest first. These reports typically originate from users or automated "
        "device warnings and can provide context for hotspot safety assessment."
    ),
    responses={
        200: {"description": "List of incidents (may be empty)"},
        404: {"description": "Hotspot has no recorded incidents"}
    }
)
async def list_for_wifi(wifi_id: str):
    rows = await models.list_incidents(wifi_id)
    return [dict(r) for r in rows]

@router.patch(
    "/{incident_id}",
    summary="Update an incident",
    description=(
        "Updates the description text of an existing incident. "
        "Retrieve incident IDs using GET /incidents/{wifi_id}."
    ),
    responses={
        200: {"description": "Incident successfully updated"},
        404: {"description": "Incident not found"},
        422: {"description": "Validation error"}
    },
    dependencies=[Depends(require_user)]
)
async def update_incident_route(
    request: Request,
    incident_id: int,
    description: str = Query(..., min_length=3, description="New description for the incident"),
):
    row = await models.update_incident(incident_id, description)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return dict(row)

@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    description=(
        "Deletes the specified incident permanently. "
        "Retrieve incident IDs using GET /incidents/{wifi_id}`."
    ),
    responses={
        204: {"description": "Incident successfully deleted"},
        404: {"description": "Incident not found"}
    },
    dependencies=[Depends(require_user)]
)
async def delete_incident_route(
    request: Request,
    incident_id: int,
):
    deleted = await models.delete_incident(incident_id)

    # Ensure correct 404 behavior
    if deleted is False:
        raise HTTPException(status_code=404, detail="Incident not found")

    return None
