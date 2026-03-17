import jwt
import os
from datetime import datetime, timedelta

SECRET = os.getenv("JWT_SECRET")
ALGO = os.getenv("JWT_ALG", "HS256")
EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", 60))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRES_MIN)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def decode_access_token(token: str):
    return jwt.decode(token, SECRET, algorithms=[ALGO])