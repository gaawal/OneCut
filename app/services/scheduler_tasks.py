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
from app.services.redis_service import redis_service
from app.utils.utils import save_weibo_data_to_redis


class SchedulerTasks:

    @staticmethod
    async def get_weibo_hotsearch():
        hotsearch_data = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            for i, hotsearch in enumerate(hotsearch_data):
                # 如果已经采集过了，更新采集状态
                if await redis_service.get(RedisKeyPrefix.WEIBO_HOT_SEARCH.format(hotsearch.get('title'))):
                    hotsearch_data[i]['collect_status'] = True
                else:
                    hotsearch_data[i]['collect_status'] = False
            await redis_service.set(RedisKeyPrefix.WEIBO_HOT_SEARCH, json.dumps(hotsearch_data, ensure_ascii=False),
                                    expire=RedisExpireTime.ONE_HOUR)

    @staticmethod
    async def get_weibo_articles_to_cache():
        try:
            cached_data = await redis_service.get(RedisKeyPrefix.WEIBO_HOT_SEARCH)  # 使用 await 关键字调用异步方法
            if cached_data:

                hotsearch_data = json.loads(cached_data)
                for item in hotsearch_data:
                    weibo_mid = item.get('mid')
                    weibo_url = item.get('url')
                    weibo_title = item.get('title')
                    logger.info(f"定时采集微博热搜话题详情-「{weibo_title}」")
                    weibo_article_cache = await redis_service.get(RedisKeyPrefix.WEIBO_HOT_SEARCH.format(weibo_title))
                    if weibo_article_cache:
                        continue
                    else:
                        if weibo_article_cache := await fetch_hot_article(weibo_mid, weibo_url):
                            logger.success(f"定时采集-{weibo_title} 成功")
                            await save_weibo_data_to_redis(weibo_title, weibo_article_cache)
                            break
                        else:
                            raise Exception(f"定时采集-{weibo_title} 失败")
        except Exception as e:
            logger.error(f"{str(e)}")
