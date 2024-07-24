# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py

import json
from typing import List

from fastapi import FastAPI
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.schemas.movies import HotSearchItem
from app.services.hotspot.weibo_article import fetch_hot_article, save_weibo_article_and_update_data
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import redis_instance


class SchedulerTasks:

    @staticmethod
    async def get_weibo_hotsearch():
        hotsearch_data: List[HotSearchItem] = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            for i, hotsearch in enumerate(hotsearch_data):
                # 如果已经采集过了，更新采集状态
                if await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(hotsearch.title)):
                    hotsearch.collect_status = True
                    hotsearch_data[i] = hotsearch
            await redis_instance.set(RedisKeyPrefix.WEIBO_HOT_SEARCH, json.dumps([item.dict() for item in hotsearch_data], ensure_ascii=False),
                                     expire=RedisExpireTime.ONE_HOUR)

    @staticmethod
    async def get_weibo_articles_to_cache():
        try:
            cached_data = await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_SEARCH)  # 使用 await 关键字调用异步方法
            if cached_data:
                hotsearch_data = json.loads(cached_data)
                for i, item in enumerate(hotsearch_data):
                    title = item.get('title')
                    url = item.get('url')
                    if not await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(title)):
                        logger.info(f"Hot article {title} need to fetched")
                        hot_article_data = await fetch_hot_article(url)
                        await save_weibo_article_and_update_data(title, hot_article_data)
                        break
        except Exception as e:
            logger.error(f"{str(e)}")
