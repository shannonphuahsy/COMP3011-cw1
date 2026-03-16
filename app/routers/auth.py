# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Form
from passlib.hash import bcrypt
from app.db.database import get_db
from app.core.auth_jwt import create_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(email: str = Form(...), password: str = Form(...)):
    db = await get_db()
    try:
        pw_hash = bcrypt.hash(password)
        row = await db.fetchrow(
            "INSERT INTO auth_user (email, password_hash) VALUES ($1, $2) RETURNING id, email, role",
            email, pw_hash
        )
        return {"message": "registered", "user": dict(row)}
    except Exception:
        raise HTTPException(status_code=400, detail="User exists or invalid input")
    finally:
        await db.close()

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    db = await get_db()
    try:
        row = await db.fetchrow("SELECT * FROM auth_user WHERE email=$1", email)
        if not row or not bcrypt.verify(password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_jwt(sub=row["email"], role=row["role"])
        return {"access_token": token, "token_type": "bearer"}
    finally:
        await db.close()