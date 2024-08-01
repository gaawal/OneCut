import ast
from abc import ABC, abstractmethod
from typing import List

from fastapi import FastAPI
from loguru import logger

from app.constant.video_const import TaskState


class BaseState(ABC):

    @abstractmethod
    async def update_task(self, task_id: str, state: int, progress: int = 0, **kwargs):
        pass

    @abstractmethod
    async def get_task(self, task_id: str):
        pass

    @abstractmethod
    async def delete_task(self, task_id: str):
        pass


class RedisService(BaseState):
    def __init__(self):
        self.redis = None

    def initialize(self, app: FastAPI):
        self.redis = app.state.redis

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

    async def get_keys(self, pattern: str) -> List[str]:
        keys = []
        cursor = b'0'
        while cursor:
            cursor, batch = await self.redis.scan(cursor=cursor, match=pattern)
            keys.extend(batch)
        return keys

    async def update_task(self, task_id: str, state: int = TaskState.PROCESSING, progress: int = 0, **kwargs):
        progress = int(progress)
        if progress > 100:
            progress = 100

        fields = {
            "state": state,
            "progress": progress,
            **kwargs,
        }

        for field, value in fields.items():
            await self.redis.hset(task_id, field, str(value))
        # Set the timeout for the task_id
        expire_time = 3600
        await self.redis.expire(task_id, expire_time)

    async def get_task(self, task_id: str):
        task_data = await self.redis.hgetall(task_id)
        if not task_data:
            return None

        task = {key: self._convert_to_original_type(value) for key, value in task_data.items()}
        return task

    async def delete_task(self, task_id: str):
        await self.redis.delete(task_id)

    @staticmethod
    def _convert_to_original_type(value):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

        if value.isdigit():
            return int(value)
        return value

    async def rpush(self, key: str, value: str):
        await self.redis.rpush(key, value)

    async def lpop(self, key: str):
        return await self.redis.lpop(key)

    async def lrem(self, key: str, count: int, value: str):
        """从任务队列中剔除key"""
        await self.redis.lrem(key, count, value)

    async def get_list(self, key: str) -> List[str]:
        """获取队列中的所有元素"""
        queue_length = await self.redis.llen(key)
        return await self.redis.lrange(key, 0, queue_length - 1)

    async def print_queue(self, key: str):
        """打印队列中的所有元素"""
        queue_items = await self.get_list(key)
        logger.info(f"当前待发布队列中的任务ID情况: {queue_items}")

redis_instance = RedisService()
