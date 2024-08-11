# -- coding: utf-8 --
# @Time : 2024/5/27 10:50
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : llm_generator.py

import json
from typing import List

from fastapi import APIRouter, Request
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.constant.video_const import CollectStatus
from app.schemas import Success
from app.schemas.movies import VideoScriptResponse, VideoScriptRequest, HotSearchItem, WeiboArticleData
from app.services.factory import llm_generator
from app.utils.crawler.weibo_crawler.weibo_article import fetch_hot_article, generate_weibo_summary, \
    save_weibo_article_and_update_data
from app.utils.crawler.weibo_crawler.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import redis_instance
from app.utils.utils import generate_md5_id

router = APIRouter()


@router.post("/scripts_terms", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
async def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    if body.weibo_title:
        # 如果要从微博热搜获取微博信息
        logger.info(f"开始获取实时微博热搜话题【{body.weibo_title}】")
        cached_data = await redis_instance.get(
            RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(body.weibo_title))  # 使用 await 关键字调用异步方法
        if cached_data:
            logger.success(f"获取微博热搜话题缓存成功【{body.weibo_title}】")
            weibo_article_data = json.loads(cached_data)
            weibo_article_data = WeiboArticleData(**weibo_article_data)
        else:
            weibo_mid = generate_md5_id(body.weibo_url)
            target_url = f'{body.weibo_url}'
            weibo_article_data = WeiboArticleData(
                weibo_mid=weibo_mid,
                url=target_url,
            )
            weibo_article_data: WeiboArticleData = await fetch_hot_article(weibo_article_data,weibo_mid,body.weibo_url)
            logger.success(f"实时获取微博热搜话题成功--{body.weibo_title}")
            await save_weibo_article_and_update_data(body.weibo_title, weibo_article_data,CollectStatus.COLLECT_OK)

            logger.success(f"微博热搜话题 {body.weibo_title} 保存redis成功.")

        weibo_summary = generate_weibo_summary(weibo_article_data)  # 假设需要获取5条评论
        # 把微博热搜作为视频主题输入
        body.video_subject = weibo_summary
    video_script, video_terms, video_title, video_tags = await llm_generator.generate_script_and_terms_async(
        video_subject=body.video_subject,
        language=body.video_language,
        paragraph_number=body.paragraph_number,
        video_category=body.video_category,
        amount=body.amount,
        word_count=body.word_count)

    response = {
        "video_title": video_title,
        "video_script": video_script,
        "video_terms": video_terms,
        "video_tags": video_tags,
    }
    return Success(data=response)


@router.post("/inspire_scripts_terms", response_model=VideoScriptResponse, summary="通过文案灵感类别为视频创建脚本以及获取对应的关键词")
async def generate_video_script_and_terms_by_inspire(request: Request, body: VideoScriptRequest):
    logger.info("Generating video by inspire，body is {}".format(body))
    video_script, video_terms, video_title, video_tags = llm_generator.generate_script_and_terms_by_inpire(
        video_inspire=body.video_inspire,
        video_inspire_keyword=body.video_inspire_keyword,
        paragraph_number=body.paragraph_number,
        amount=body.amount,
        word_count=body.word_count)
    response = {
        "video_title": video_title,
        "video_script": video_script,
        "video_terms": video_terms,
        "video_tags": video_tags,
    }
    return Success(data=response)


@router.post("/refine-scripts", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    origin_script = body.origin_script
    video_category = body.video_category
    word_count = body.word_count
    refine_script = llm_generator.refine_scripts(original_script=origin_script, video_category=video_category,
                                                 word_count=word_count
                                                 )
    response = {
        "video_script": refine_script,

    }
    return Success(data=response)


@router.post("/continue-scripts", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    origin_script = body.origin_script
    video_category = body.video_category
    word_count = body.word_count
    continue_script = llm_generator.continue_scripts(original_script=origin_script, video_category=video_category,
                                                     word_count=word_count)
    response = {
        "video_script": continue_script,

    }
    return Success(data=response)


@router.get("/hot-spot", response_model=VideoScriptResponse, summary="搜索新闻热点")
async def get_hot_spot(request: Request):
    cached_data = await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_SEARCH)
    if cached_data:
        logger.info("获取微博热搜redis缓存")
        hotsearch_data = json.loads(cached_data)
    else:
        hotsearch_data: List[HotSearchItem] = await get_weibo_hotsearch()
        if hotsearch_data:
            for i, hotsearch in enumerate(hotsearch_data):
                if await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(hotsearch.title)):
                    hotsearch.collect_status = CollectStatus.COLLECT_OK
            hotsearch_data = [item.dict() for item in hotsearch_data]
            await redis_instance.set(
                RedisKeyPrefix.WEIBO_HOT_SEARCH,
                json.dumps(hotsearch_data, ensure_ascii=False),
                expire=RedisExpireTime.THIRTY_MINUTES
            )
    return Success(data=hotsearch_data)
