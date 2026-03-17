from fastapi import Header, HTTPException
import os

API_KEY = os.getenv("API_KEY")

async def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API Key")
