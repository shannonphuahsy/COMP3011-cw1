# app/main.py
import app
from fastapi import FastAPI, HTTPException
from app.db.database import get_db

# Routers
from app.routers.wifi_networks import router as wifi_router
from app.routers.analytics import router as analytics_router
from app.routers.incidents import router as incidents_router
from app.routers.assessments import router as assess_router
from app.routers.auth import router as auth_router

# SlowAPI
from app.core.limiter import (
    limiter,
    _rate_limit_exceeded_handler,
    SlowAPIMiddleware,
    ENABLED
)
from slowapi.errors import RateLimitExceeded

# OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI(
    title="Geospatial Risk Analysis for Public WiFi Networks",
    version="1.0.0",
)

# -----------------------------------------
# ROUTERS
# -----------------------------------------
app.include_router(auth_router)
app.include_router(wifi_router)
app.include_router(analytics_router)
app.include_router(incidents_router)
app.include_router(assess_router)


# -----------------------------------------
# HEALTH ENDPOINTS
# -----------------------------------------

@app.get("/livez")
async def livez():
    return {"status": "alive"}

@app.get("/readyz")
async def readyz():
    try:
        conn = await get_db()
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(503, "not ready")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# -----------------------------------------
# SlowAPI global setup
# -----------------------------------------

if ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

# -----------------------------------------
# OpenTelemetry
# -----------------------------------------

FastAPIInstrumentor.instrument_app(app)