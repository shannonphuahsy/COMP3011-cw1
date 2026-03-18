# app/main.py

from fastapi import FastAPI, HTTPException
from app.db.database import get_db

# Routers
from app.routers.internal import router as internal_router
from app.routers.wifi_networks import router as wifi_router
from app.routers.analytics import router as analytics_router
from app.routers.incidents import router as incidents_router
from app.routers.assessments import router as assess_router
from app.routers.auth import router as auth_router  # ← ADDED

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
app.include_router(auth_router)       # ← ADDED
app.include_router(wifi_router)
app.include_router(analytics_router)
app.include_router(incidents_router)
app.include_router(assess_router)
app.include_router(internal_router)

# -----------------------------------------
# HEALTH ENDPOINTS
# -----------------------------------------
@app.get("/")
def root():
    return {"message": "API is running"}
@app.get("/livez")
async def livez():
    return {"status": "alive"}


@app.get("/readyz")
async def readyz():
    try:
        async for conn in get_db():
            await conn.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        print("DB connection failed:", e)
        return {"status": "not ready"}


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