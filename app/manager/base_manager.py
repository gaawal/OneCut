import threading
from typing import Callable, Any, Dict
from loguru import logger
from app.settings.config import settings
import asyncio

class TaskManager:
    def __init__(self):
        self.max_concurrent_tasks = settings._max_concurrent_tasks
        self.current_tasks = 0
        self.lock = threading.Lock()
        self.queue = self.create_queue()

    def create_queue(self):
        raise NotImplementedError()

    def add_task(self, func: Callable, *args: Any, **kwargs: Any):
        with self.lock:
            if self.current_tasks < self.max_concurrent_tasks:
                logger.info(f"add task: {func.__name__}, current_tasks: {self.current_tasks}")
                self.execute_task(func, *args, **kwargs)
            else:
                logger.info(f"enqueue task: {func.__name__}, current_tasks: {self.current_tasks}")
                self.enqueue({"func": func, "args": args, "kwargs": kwargs})

    def execute_task(self, func: Callable, *args: Any, **kwargs: Any):
        thread = threading.Thread(target=self.run_task, args=(func, *args), kwargs=kwargs)
        thread.start()

    def run_task(self, func: Callable, *args: Any, **kwargs: Any):
        try:
            with self.lock:
                self.current_tasks += 1

            if asyncio.iscoroutinefunction(func):
                # 为每个线程创建一个新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(func(*args, **kwargs))
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            else:
                func(*args, **kwargs)
        finally:
            self.task_done()

    def check_queue(self):
        with self.lock:
            if self.current_tasks < self.max_concurrent_tasks and not self.is_queue_empty():
                task_info = self.dequeue()
                func = task_info['func']
                args = task_info.get('args', ())
                kwargs = task_info.get('kwargs', {})
                self.execute_task(func, *args, **kwargs)

    def task_done(self):
        with self.lock:
            self.current_tasks -= 1
        self.check_queue()

    def enqueue(self, task: Dict):
        raise NotImplementedError()

    def dequeue(self):
        raise NotImplementedError()

    def is_queue_empty(self):
        raise NotImplementedError()
