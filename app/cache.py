# app/cache.py

import redis.asyncio as redis

# Local Redis default. Change to Upstash if needed.
_redis = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True
)

async def cache_get(key: str):
    return await _redis.get(key)

async def cache_setex(key: str, ttl_seconds: int, value: str):
    await _redis.setex(key, ttl_seconds, value)