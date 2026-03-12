# app/main.py
from fastapi import FastAPI
from app.routers.wifi_networks import router as wifi_router
from app.routers.analytics import router as analytics_router
from app.routers.incidents import router as incidents_router
from app.routers.assessments import router as assess_router


openapi_tags = [
    {"name": "WiFi", "description": "Read official hotspot data and perform limited operational updates."},
    {"name": "Analytics", "description": "Geospatial search, ranking, and crime context."},
    {"name": "Assessments", "description": "BSSID‑triggered safety reports for users connecting to public Wi‑Fi."},
    {"name": "Incidents", "description": "User‑reported safety incidents (full CRUD model)."},
    {"name": "System", "description": "Health and readiness probes."},
]

app = FastAPI(
    title="Geospatial Risk Analysis for Public WiFi Networks",
    version="1.0.0",
    description=(
        "An API that aggregates public Wi‑Fi hotspot data with crime and population context,\n"
        "and returns geospatial safety analytics for users connecting to public Wi‑Fi."
    ),
    contact={"name": "Your Name", "email": "you@example.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.include_router(wifi_router)
app.include_router(analytics_router)
app.include_router(incidents_router)
app.include_router(assess_router)

@app.get(
    "/healthz",
    tags=["System"],
    summary="Service health probe",
    description="Returns **200 OK** if the API process is alive and responding."
)
def healthz():
    return {"status": "ok"}