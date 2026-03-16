# app/core/auth_api_key.py
import os
from fastapi import Header, HTTPException, status

API_KEY = os.getenv("API_KEY")

async def require_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API is misconfigured: API_KEY not set"
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return {"method": "api_key"}