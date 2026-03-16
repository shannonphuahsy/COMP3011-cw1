# app/routers/incidents.py

from fastapi import APIRouter, HTTPException, status, Request
from app.db import models
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.core.limiter import limiter  # unified SlowAPI limiter

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


# --------------------------------------------------------------
# CREATE INCIDENT
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
@limiter.limit("10/minute")  # per-IP create limit
async def create_incident_route(
    request: Request,
    payload: IncidentCreate
):
    """
    Create a new safety incident linked to a hotspot/BSSID.
    """
    row = await models.create_incident(
        payload.wifi_id,
        payload.bssid,
        payload.description
    )
    return dict(row)


# --------------------------------------------------------------
# LIST INCIDENTS FOR A HOTSPOT
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
# UPDATE INCIDENT
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
@limiter.limit("10/minute")  # per-IP update limit
async def update_incident_route(
    request: Request,
    incident_id: int,
    body: IncidentUpdate
):
    row = await models.update_incident(incident_id, body.description)
    if not row:
        raise HTTPException(404, "Incident not found")
    return dict(row)


# --------------------------------------------------------------
# DELETE INCIDENT
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
@limiter.limit("10/minute")  # per-IP delete limit
async def delete_incident_route(
    request: Request,
    incident_id: int
):
    await models.delete_incident(incident_id)
    return None