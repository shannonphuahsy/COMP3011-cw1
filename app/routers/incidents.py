# app/routers/incidents.py

from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from app.db import models
from app.core.limiter import limiter  # unified SlowAPI limiter
from app.services.dependencies import require_user  # ← ADDED

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)

# --------------------------------------------------------------
# CREATE INCIDENT  (NOW USING QUERY PARAMETERS)
# --------------------------------------------------------------

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


# --------------------------------------------------------------
# LIST INCIDENTS FOR A HOTSPOT  (PUBLIC — UNCHANGED)
# --------------------------------------------------------------

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
        404: {"description": "Hotspot has no recorded incidents (optional)"}
    }
)
async def list_for_wifi(wifi_id: str):
    rows = await models.list_incidents(wifi_id)
    return [dict(r) for r in rows]


# --------------------------------------------------------------
# UPDATE INCIDENT  (NOW USING QUERY PARAMETER)
# --------------------------------------------------------------

@router.patch(
    "/{incident_id}",
    summary="Update an incident",
    description=(
        "Updates the **description** text of an existing incident. This is typically used "
        "when refining the original report, fixing typos, or adding clarifications. "
        "The hotspot association cannot be changed."
    ),
    responses={
        200: {"description": "Incident successfully updated"},
        404: {"description": "Incident not found"},
        422: {"description": "Validation error"}
    }
)
@limiter.limit("10/minute")
async def update_incident_route(
    request: Request,
    incident_id: int,
    description: str = Query(..., min_length=3, description="New description for the incident"),
    user=Depends(require_user)  # ← ADDED
):
    row = await models.update_incident(incident_id, description)
    if not row:
        raise HTTPException(404, "Incident not found")
    return dict(row)


# --------------------------------------------------------------
# DELETE INCIDENT  (AUTH REQUIRED — UNCHANGED INPUT)
# --------------------------------------------------------------

@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    description=(
        "Deletes the specified incident permanently. This operation is irreversible and "
        "typically restricted to administrative tools or automated cleanup tasks."
    ),
    responses={
        204: {"description": "Incident successfully deleted"},
        404: {"description": "Incident not found"}
    }
)
@limiter.limit("10/minute")
async def delete_incident_route(
    request: Request,
    incident_id: int,
    user=Depends(require_user)  # ← ADDED
):
    await models.delete_incident(incident_id)
    return None