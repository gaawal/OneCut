import ast
from abc import ABC, abstractmethod

from fastapi import FastAPI

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


redis_instance = RedisService()
