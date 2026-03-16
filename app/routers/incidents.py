# app/routers/incidents.py

from fastapi import APIRouter, HTTPException, status, Request, Depends
from app.db import models
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.core.limiter import limiter  # unified SlowAPI limiter

# Auth: combined OR, and JWT for writes
from app.core.auth_combined import require_api_key_or_jwt
from app.core.auth_jwt import require_user, require_role

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)

# --------------------------------------------------------------
# CREATE INCIDENT (JWT required)
# --------------------------------------------------------------
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new safety incident",
    description=(
        "Creates a user‑reported safety incident associated with a hotspot via `wifi_id` and `bssid`. "
        "This contributes to community safety signals and does not alter authoritative hotspot metadata."
    ),
    responses={
        201: {"description": "Incident successfully created"},
        422: {"description": "Validation error (missing or invalid fields)"}
    },
    dependencies=[Depends(require_user)]  # JWT only
)
@limiter.limit("10/minute")
async def create_incident_route(
    request: Request,
    payload: IncidentCreate
):
    row = await models.create_incident(
        payload.wifi_id,
        payload.bssid,
        payload.description
    )
    return dict(row)

# --------------------------------------------------------------
# LIST INCIDENTS FOR A HOTSPOT (API Key OR JWT)
# --------------------------------------------------------------
@router.get(
    "/{wifi_id}",
    summary="List incidents for a hotspot",
    description=(
        "Returns incidents associated with the given `wifi_id` (newest first). "
        "Useful for contextualising risk around public Wi‑Fi usage."
    ),
    responses={
        200: {"description": "List of incidents (may be empty)"},
        404: {"description": "Hotspot has no recorded incidents (optional)"}
    },
    dependencies=[Depends(require_api_key_or_jwt)]  # API Key OR JWT
)
async def list_for_wifi(wifi_id: str):
    rows = await models.list_incidents(wifi_id)
    return [dict(r) for r in rows]

# --------------------------------------------------------------
# UPDATE INCIDENT (JWT required)
# --------------------------------------------------------------
@router.patch(
    "/{incident_id}",
    summary="Update an incident",
    description=(
        "Updates the incident `description`. Use to refine reports, correct typos, or add detail."
    ),
    responses={
        200: {"description": "Incident successfully updated"},
        404: {"description": "Incident not found"},
        422: {"description": "Validation error"}
    },
    dependencies=[Depends(require_user)]  # JWT only
)
@limiter.limit("10/minute")
async def update_incident_route(
    request: Request,
    incident_id: int,
    body: IncidentUpdate
):
    row = await models.update_incident(incident_id, body.description)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return dict(row)

# --------------------------------------------------------------
# DELETE INCIDENT (Admin only via JWT role)
#   If you don't need admin role, change to: dependencies=[Depends(require_user)]
# --------------------------------------------------------------
@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    description=(
        "Permanently deletes the specified incident. Typically restricted to administrative tools or moderation flows."
    ),
    responses={
        204: {"description": "Incident successfully deleted"},
        404: {"description": "Incident not found"}
    },
    dependencies=[Depends(require_role("admin"))]  # JWT admin
)
@limiter.limit("10/minute")
async def delete_incident_route(
    request: Request,
    incident_id: int
):
    await models.delete_incident(incident_id)
    return None