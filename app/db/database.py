# app/db/database.py

import asyncpg
import os
import ssl

# --------------------------------------
# Load DATABASE_URL
# --------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Fix postgres:// → postgresql:// (required for asyncpg)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Global connection pool
pool = None


# --------------------------------------
# Connect to DB (called on startup)
# --------------------------------------
async def connect_to_db():
    global pool

    print("\n======================================")
    print("Connecting to PostgreSQL…")
    print("DATABASE_URL =", DATABASE_URL)
    print("======================================\n")

    try:
        # Detect Railway by hostname
        is_railway = ".railway.app" in DATABASE_URL

        if is_railway:
            print("→ Environment: Railway")
            print("→ Using SSL (no certificate verification)")

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            pool = await asyncpg.create_pool(
                DATABASE_URL,
                ssl=ssl_context,
                min_size=1,
                max_size=10,
            )

        else:
            print("→ Environment: Local development")
            print("→ Using NO SSL")

            pool = await asyncpg.create_pool(
                DATABASE_URL,
                ssl=False,
                min_size=1,
                max_size=10,
            )

        print("✔ Database pool created successfully\n")

    except Exception as e:
        print("✘ Failed to connect to database:", e)
        pool = None


# --------------------------------------
# Disconnect from DB (called on shutdown)
# --------------------------------------
async def disconnect_db():
    global pool
    if pool:
        await pool.close()
        print("Database pool closed")


# --------------------------------------
# Dependency for FastAPI routes
# --------------------------------------
async def get_db():
    if not pool:
        raise Exception("Database pool not initialized")

    async with pool.acquire() as connection:
        yield connection