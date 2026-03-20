# app/routers/auth.py

from fastapi import APIRouter, HTTPException, Query
from app.schemas.auth import TokenResponse
from app.services.auth_utils import hash_password, verify_password
from app.services.jwt_service import create_access_token
from app.db.database import get_db

router = APIRouter(prefix="/auth", tags=["Authorization"])


# --------------------------------------------------------------
# SIGNUP (query parameters)
# --------------------------------------------------------------
@router.post("/signup")
async def signup(
    email: str = Query(..., description="User email"),
    password: str = Query(..., description="User password (will be hashed)")
):
    db = await get_db()
    try:
        # --- Check if user already exists (409 Conflict)
        existing = await db.fetchrow(
            "SELECT id FROM auth_user WHERE email=$1;",
            email
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists."
            )

        # --- Create new user
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
# LOGIN (query parameters)
# --------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    email: str = Query(..., description="User email"),
    password: str = Query(..., description="User password")
):
    db = await get_db()
    try:
        # Look up user by email
        row = await db.fetchrow(
            "SELECT id, email, password_hash, role FROM auth_user WHERE email=$1",
            email,
        )

        # --- Standardised 401: wrong email or no such user
        if not row:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials."
            )

        # --- Standardised 401: wrong password
        if not verify_password(password, row["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials."
            )

        # Create JWT token
        token = create_access_token({
            "sub": row["email"],
            "role": row["role"],
            "user_id": row["id"]
        })

        return {"access_token": token}

    finally:
        await db.close()