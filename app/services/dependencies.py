# app/services/dependencies.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from app.services.jwt_service import decode_access_token

security = HTTPBearer()

async def require_user(credentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        return payload     # contains user_id, email, role (role unused now)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")