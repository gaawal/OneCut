import ast
from abc import ABC, abstractmethod

import redis

from app.constant.video_const import TaskState
from app.settings.config import settings


# Base class for state management
class BaseState(ABC):

    @abstractmethod
    def update_task(self, task_id: str, state: int, progress: int = 0, **kwargs):
        pass

    @abstractmethod
    def get_task(self, task_id: str):
        pass

# Redis state management
class RedisState(BaseState):

    def __init__(self):

        redis_url = settings.REDIS_URL
        self._redis = redis.Redis.from_url(redis_url)

    def update_task(self, task_id: str, state: int = TaskState.PROCESSING, progress: int = 0, **kwargs):
        progress = int(progress)
        if progress > 100:
            progress = 100

        fields = {
            "state": state,
            "progress": progress,
            **kwargs,
        }

        for field, value in fields.items():
            self._redis.hset(task_id, field, str(value))
        # Set the timeout for the task_id
        expire_time = 3600
        self._redis.expire(task_id,expire_time)
    def get_task(self, task_id: str):
        task_data = self._redis.hgetall(task_id)
        if not task_data:
            return None

        task = {key.decode('utf-8'): self._convert_to_original_type(value) for key, value in task_data.items()}
        return task

    def delete_task(self, task_id: str):
        self._redis.delete(task_id)

    @staticmethod
    def _convert_to_original_type(value):
        """
        Convert the value from byte string to its original data type.
        You can extend this method to handle other data types as needed.
        """
        value_str = value.decode('utf-8')

        try:
            # try to convert byte string array to list
            return ast.literal_eval(value_str)
        except (ValueError, SyntaxError):
            pass

        if value_str.isdigit():
            return int(value_str)
        # Add more conversions here if needed
        return value_str


state = RedisState()
