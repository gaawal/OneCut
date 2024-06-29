import json
from typing import Dict

import redis

from app.settings.config import settings
from app.manager.base_manager import TaskManager
from app.schemas.movies import VideoParams
from app.services import task as tm

FUNC_MAP = {
    'start': tm.start,
    # 'start_test': tm.start_test
}


class RedisTaskManager(TaskManager):
    def __init__(self):
        redis_url = settings.REDIS_URL
        self.redis_client = redis.Redis.from_url(redis_url)
        super().__init__()

    def create_queue(self):
        return "task_queue"

    def enqueue(self, task: Dict):
        task_with_serializable_params = task.copy()
        if 'params' in task['kwargs'] and isinstance(task['kwargs']['params'], VideoParams):
            task_with_serializable_params['kwargs']['params'] = task['kwargs']['params'].dict()
        task_with_serializable_params['func'] = task['func'].__name__
        self.redis_client.rpush(self.queue, json.dumps(task_with_serializable_params))

    def dequeue(self):
        task_json = self.redis_client.lpop(self.queue)
        if task_json:
            task_info = json.loads(task_json)
            task_info['func'] = FUNC_MAP[task_info['func']]
            if 'params' in task_info['kwargs'] and isinstance(task_info['kwargs']['params'], dict):
                task_info['kwargs']['params'] = VideoParams(**task_info['kwargs']['params'])
            return task_info
        return None

    def is_queue_empty(self):
        return self.redis_client.llen(self.queue) == 0
