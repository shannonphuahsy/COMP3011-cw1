# app/routers/auth.py

from fastapi import APIRouter, HTTPException, Query
from app.schemas.auth import TokenResponse
from app.services.auth_utils import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.db.database import get_db

router = APIRouter(prefix="/auth", tags=["Authorization"])


# --------------------------------------------------------------
# SIGNUP (now using query parameters instead of request body)
# --------------------------------------------------------------

@router.post("/signup")
async def signup(
    email: str = Query(..., description="User email"),
    password: str = Query(..., description="User password (will be hashed)")
):
    db = await get_db()
    try:
        hashed = hash_password(password)

        row = await db.fetchrow(
            """
            INSERT INTO auth_user (email, password_hash)
            VALUES ($1, $2)
            RETURNING id, email, role
            """,
            email,
            hashed
        )
        return dict(row)
    finally:
        await db.close()


# --------------------------------------------------------------
# LOGIN (now using query parameters instead of request body)
# --------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(
    email: str = Query(..., description="User email"),
    password: str = Query(..., description="User password")
):
    db = await get_db()
    try:
        row = await db.fetchrow(
            "SELECT id, email, password_hash, role FROM auth_user WHERE email=$1",
            email,
        )
        if not row:
            raise HTTPException(401, "Invalid credentials")

        if not verify_password(password, row["password_hash"]):
            raise HTTPException(401, "Invalid credentials")

        token = create_access_token({
            "sub": row["email"],
            "role": row["role"],
            "user_id": row["id"]
        })

        return {"access_token": token}
    finally:
        await db.close()