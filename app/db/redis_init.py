import aioredis

from app.settings.config import settings


class RedisClient:
    def __init__(self):
        self.redis = None

    async def init_redis_pool(self):
        self.redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def close_redis_pool(self):
        await self.redis.close()


# 使用单例模式来确保全局唯一的Redis客户端实例
redis_client = RedisClient()

