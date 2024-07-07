import json
import redis
from typing import Dict
from loguru import logger
from app.settings.config import settings
from app.manager.base_manager import TaskManager
from app.schemas.movies import VideoParams
from app.services import task as tm

FUNC_MAP = {
    'start': tm.start,
    # 'start_test': tm.start_test
}

class RedisTaskManager(TaskManager):
    def __init__(self, redis_url: str = settings.REDIS_URL):
        try:
            self.redis_client = redis.Redis.from_url(redis_url)
            super().__init__()
            logger.info("Connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def create_queue(self):
        return "task_queue"

    def enqueue(self, task: Dict):
        try:
            task_with_serializable_params = task.copy()
            if 'params' in task['kwargs'] and isinstance(task['kwargs']['params'], VideoParams):
                task_with_serializable_params['kwargs']['params'] = task['kwargs']['params'].dict()
            task_with_serializable_params['func'] = task['func'].__name__
            self.redis_client.rpush(self.queue, json.dumps(task_with_serializable_params))
            logger.info(f"Enqueued task: {task_with_serializable_params}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {str(e)}")

    def dequeue(self):
        try:
            task_json = self.redis_client.lpop(self.queue)
            if task_json:
                task_info = json.loads(task_json)
                task_info['func'] = FUNC_MAP[task_info['func']]
                if 'params' in task_info['kwargs'] and isinstance(task_info['kwargs']['params'], dict):
                    task_info['kwargs']['params'] = VideoParams(**task_info['kwargs']['params'])
                logger.info(f"Dequeued task: {task_info}")
                return task_info
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue task: {str(e)}")
            return None

    def is_queue_empty(self):
        try:
            queue_length = self.redis_client.llen(self.queue)
            logger.info(f"当前待生成视频任务个数为 {queue_length}")
            return queue_length == 0
        except Exception as e:
            logger.error(f"Failed to check if queue is empty: {str(e)}")
            return True
