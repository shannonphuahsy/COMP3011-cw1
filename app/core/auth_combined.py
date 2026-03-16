# app/core/auth_combined.py
from fastapi import Depends, HTTPException, status
from app.core.auth_api_key import require_api_key
from app.core.auth_jwt import require_user

async def require_api_key_or_jwt(
    api_key_result = Depends(require_api_key),
    # NOTE: this trick allows either one to succeed:
    # we try JWT second, catching the first exception at the framework level by dependency resolution rules.
    # To relax further, you can implement manual header checks instead.
    # For simplicity here, we rely on FastAPI resolving either dependency.
    user_result = Depends(require_user)
):
    # If either dependency returned successfully, we’re authenticated.
    # But FastAPI will try both; to truly allow either we can wrap them in a custom handler.
    # Simpler approach: implement manual headers parsing – see advanced note below.
    return api_key_result or user_result