# -- coding: utf-8 --
# @Time : 2024/6/30 13:34
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : images_generator.py

import json

from fastapi import Request
from loguru import logger

from app.constant.redis_const import RedisKeyPrefix
from app.schemas.movies import VideoParams
from app.services.redis_service import redis_instance


async def get_images_files(params: VideoParams):
    logger.info(f"get images file begin,weibo title is {params.weibo_title}")
    images_path = []
    if params.weibo_title:
        logger.info(f"从微博热搜获取图片素材")
        # 从微博热搜获取图片素材
        cache_weibo_article_key = RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(params.weibo_title)
        cached_data = await redis_instance.get(cache_weibo_article_key)
        images_path = []
        if cached_data:
            logger.success(f'获取微博热搜文章素材缓存成功，redis key is {cache_weibo_article_key}')
            article_info = json.loads(cached_data)
            articles = article_info.get('articles')

            for i in articles:
                screenshot_images_path: str = i.get('screenshot_path')
                weibo_images_list: list = i.get('images')
                if screenshot_images_path:
                    images_path.append(screenshot_images_path)
                if weibo_images_list:
                    images_path.extend(weibo_images_list)
            logger.info(f'使用的微博图片素材资源数量:{len(images_path)}条')

    return images_path
