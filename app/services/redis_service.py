from redis.asyncio import Redis

class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def set(self, key: str, value: str, expire: int = None):
        await self.redis.set(key, value)
        if expire:
            await self.redis.expire(key, expire)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def hset(self, hash_key: str, field: str, value: str, expire: int = None):
        await self.redis.hset(hash_key, field, value)
        if expire:
            await self.redis.expire(hash_key, expire)

    async def hget(self, hash_key: str, field: str):
        return await self.redis.hget(hash_key, field)
