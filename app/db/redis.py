import redis.asyncio as redis
from app.settings.config import settings

redis_client: redis.Redis = None

async def get_redis() -> redis.Redis:
    return redis_client

async def init_redis_pool():
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL,encoding="utf-8", decode_responses=True)

async def close_redis_pool():
    global redis_client
    if redis_client:
        await redis_client.close()
