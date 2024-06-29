# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py
# @Software: PyCharm
import json

from fastapi import FastAPI

from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import RedisService

REDIS_HOTSEARCH_KEY = "weibo_hotsearch"
class SchedulerTasks:

    @staticmethod
    async def get_weibo_hotsearch(app: FastAPI):
        redis_service = RedisService(app.state.redis)
        hotsearch_data = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            await redis_service.set(REDIS_HOTSEARCH_KEY, json.dumps(hotsearch_data, ensure_ascii=False), expire=1800)