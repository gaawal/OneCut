import json
import multiprocessing
from typing import Callable, Any, Dict
from fastapi import FastAPI
from loguru import logger
from app.schemas.movies import VideoParams
from app.services import video_controller as generate_video_task
import asyncio

FUNC_MAP = {
    'start': generate_video_task.start,
    # 添加其他任务处理函数的映射
}


class RedisTaskManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisTaskManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.max_concurrent_tasks = 1  # 根据CPU核心数设置最大并发任务数
        logger.info(f"CPU最大核心数是：{self.max_concurrent_tasks}")
        self.current_tasks = 0
        self.lock = asyncio.Lock()
        self.queue = "task_queue"
        self.redis_client = None

    def initialize(self, app: FastAPI):
        self.redis_client = app.state.redis

    async def add_task(self, func: Callable, *args: Any, **kwargs: Any):
        async with self.lock:
            if self.current_tasks < self.max_concurrent_tasks:
                logger.info(f"任务队列添加视频生成任务: {func.__name__}, 当前待处理任务数: {self.current_tasks}")
                await self.execute_task(func, *args, **kwargs)
            else:
                logger.info(f"Enqueuing task: {func.__name__}, current tasks: {self.current_tasks}")
                await self.enqueue({"func": func, "args": args, "kwargs": self.sanitize_kwargs(kwargs)})

    async def execute_task(self, func: Callable, *args: Any, **kwargs: Any):
        asyncio.create_task(self.run_task(func, *args, **kwargs))

    async def run_task(self, func: Callable, *args: Any, **kwargs: Any):
        try:
            async with self.lock:
                self.current_tasks += 1

            await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task {func.__name__} raised an exception: {e}")
        finally:
            await self.task_done()

    async def check_queue(self):
        async with self.lock:
            if self.current_tasks < self.max_concurrent_tasks and not await self.is_queue_empty():
                task_info = await self.dequeue()
                if task_info:
                    func = task_info['func']
                    args = task_info.get('args', ())
                    kwargs = task_info.get('kwargs', {})
                    await self.execute_task(func, *args, **kwargs)

    async def task_done(self):
        async with self.lock:
            self.current_tasks -= 1
        await self.check_queue()

    def sanitize_kwargs(self, kwargs: Dict) -> Dict:
        sanitized = {}
        for key, value in kwargs.items():
            if isinstance(value, VideoParams):
                sanitized[key] = value.dict()
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_kwargs(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized

    async def enqueue(self, task: Dict):
        try:
            task_with_serializable_params = task.copy()
            task_with_serializable_params['func'] = task['func'].__name__
            await self.redis_client.rpush(self.queue, json.dumps(task_with_serializable_params))
            logger.info(f"Enqueued task: {task_with_serializable_params}")
        except Exception as e:
            logger.error(f"Failed to enqueue task: {str(e)}")

    async def dequeue(self):
        try:
            task_json = await self.redis_client.lpop(self.queue)
            if task_json:
                task_info = json.loads(task_json)
                task_info['func'] = FUNC_MAP.get(task_info['func'])
                if not task_info['func']:
                    logger.error(f"Function {task_info['func']} not found in FUNC_MAP")
                    return None
                if 'params' in task_info['kwargs'] and isinstance(task_info['kwargs']['params'], dict):
                    task_info['kwargs']['params'] = VideoParams(**task_info['kwargs']['params'])
                logger.info(f"生成视频任务加入队列")
                return task_info
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue task: {str(e)}")
            return None

    async def is_queue_empty(self):
        try:
            queue_length = await self.redis_client.llen(self.queue)
            logger.info(f"当前待生成视频任务个数为 {queue_length}")
            return queue_length == 0
        except Exception as e:
            logger.error(f"Failed to check if queue is empty: {str(e)}")
            return True


# 实例化 RedisTaskManager
redis_taskmanager = RedisTaskManager()
