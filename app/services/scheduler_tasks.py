# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py

import json

from fastapi import FastAPI
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.services.hotspot.weibo_article import fetch_hot_article
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import redis_instance
from app.utils.utils import save_weibo_article_and_update_data


class SchedulerTasks:

    @staticmethod
    async def get_weibo_hotsearch():
        hotsearch_data = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            for i, hotsearch in enumerate(hotsearch_data):
                # 如果已经采集过了，更新采集状态
                if await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(hotsearch.get('title'))):
                    print("定时采集过了")
                    hotsearch_data[i]['collect_status'] = True
                else:
                    print("定时采集没有")
                    hotsearch_data[i]['collect_status'] = False
            await redis_instance.set(RedisKeyPrefix.WEIBO_HOT_SEARCH, json.dumps(hotsearch_data, ensure_ascii=False),
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
                    else:
                        logger.info(f"Hot article {title} have already fetched")



        except Exception as e:
            logger.error(f"{str(e)}")
