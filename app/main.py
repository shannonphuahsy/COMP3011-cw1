# app/main.py
from fastapi import FastAPI
from app.routers.wifi_networks import router as wifi_router
from app.routers.analytics import router as analytics_router
from app.routers.incidents import router as incidents_router
from app.routers.assessments import router as assess_router

app = FastAPI(
    title="Geospatial Risk Analysis for Public WiFi Networks",
    version="1.0.0",
    description="Safety analytics and risk scoring for public WiFi"
)

app.include_router(wifi_router)
app.include_router(analytics_router)
app.include_router(incidents_router)
app.include_router(assess_router)

@app.get("/healthz", tags=["System"])
def healthz():
    return {"status": "ok"}