import asyncpg
import os
import ssl

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Fix postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

pool = None  # global pool


async def connect_to_db():
    global pool

    print("Connecting using:", DATABASE_URL)

    try:
        # Detect if we are in Railway (host contains ".railway.app")
        if ".railway.app" in DATABASE_URL:
            print("Using Railway PostgreSQL with SSL…")

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
            # Local development DB
            print("Using local PostgreSQL (no SSL)…")

            pool = await asyncpg.create_pool(
                DATABASE_URL,
                ssl=False,
                min_size=1,
                max_size=10,
            )

        print("Database pool created successfully")

    except Exception as e:
        print("Failed to connect to database:", e)
        pool = None