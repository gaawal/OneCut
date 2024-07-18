# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py
# @Software: PyCharm
import json

from fastapi import FastAPI
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.services.hotspot.weibo_article import fetch_hot_article
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import RedisService

REDIS_HOTSEARCH_KEY = RedisKeyPrefix.WEIBO_HOT_SEARCH
REDIS_HOT_ARTICLE_KEY = RedisKeyPrefix.WEIBO_HOT_ARTICLE


class SchedulerTasks:

    @staticmethod
    async def get_weibo_hotsearch(app: FastAPI):
        redis_service = RedisService(app.state.redis)
        hotsearch_data = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            await redis_service.set(REDIS_HOTSEARCH_KEY, json.dumps(hotsearch_data, ensure_ascii=False),
                                    expire=RedisExpireTime.THIRTY_MINUTES)


    @staticmethod
    async def get_weibo_articles_to_cache(app: FastAPI):
        try:
            redis_service = RedisService(app.state.redis)
            cached_data = await redis_service.get(REDIS_HOTSEARCH_KEY)  # 使用 await 关键字调用异步方法
            if cached_data:
                logger.info("定时采集微博热搜话题详情")
                hotsearch_data = json.loads(cached_data)
                for item in hotsearch_data:
                    weibo_mid = item.get('mid')
                    weibo_url = item.get('url')
                    weibo_title = item.get('title')
                    weibo_article_cache = await redis_service.get(REDIS_HOT_ARTICLE_KEY.format(weibo_mid))
                    if weibo_article_cache:
                        logger.warning(f"{weibo_mid}:{weibo_title}已采集成功，无需重复采集")
                        continue
                    else:
                        if await fetch_hot_article(weibo_mid, weibo_url):
                            logger.success(f"定时采集---{weibo_mid} {weibo_title} 成功")
                            break
                        else:
                            raise Exception(f"定时采集---{weibo_mid} {weibo_title} 失败")
        except Exception as e:
            logger.error(f"{str(e)}")

