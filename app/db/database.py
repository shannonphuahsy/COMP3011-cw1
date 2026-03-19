# app/db/database.py
import asyncpg
import os
import ssl

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Railway sometimes provides postgres:// instead of postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

pool = None  # global connection pool


async def connect_to_db():
    global pool
    try:
        print("Connecting to database...")

        # SSL required for Railway PostgreSQL
        ssl_context = ssl.create_default_context()

        pool = await asyncpg.create_pool(
            DATABASE_URL,
            ssl=ssl_context,
            min_size=1,
            max_size=10
        )

        print("Database pool created successfully")

    except Exception as e:
        print("Failed to connect to database:", e)
        pool = None


async def disconnect_db():
    global pool
    if pool:
        await pool.close()
        print("Database pool closed")


async def get_db():
    if not pool:
        raise Exception("Database pool not initialized")

    async with pool.acquire() as connection:
        yield connection