# app/core/auth_jwt.py
import os, time, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-secret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

bearer_scheme = HTTPBearer(auto_error=False)

def create_jwt(sub: str, role: str = "user") -> str:
    now = int(time.time())
    payload = {"sub": sub, "role": role, "iat": now, "exp": now + JWT_EXPIRES_MIN * 60}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    claims = verify_jwt(credentials.credentials)
    return {"method": "jwt", "claims": claims}

def require_role(role: str):
    async def dependency(user=Depends(require_user)):
        claims = user["claims"]
        if claims.get("role") != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dependency