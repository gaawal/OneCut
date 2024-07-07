# -- coding: utf-8 --
# @Time : 2024/5/27 10:50
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : llm.py
# @Software: PyCharm
import json

from fastapi import APIRouter, Request
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.schemas import Success
from app.schemas.movies import VideoScriptResponse, VideoScriptRequest
from app.services import llm
from app.services.hotspot.weibo_article import fetch_hot_article, generate_weibo_summary
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.utils.redis import get_redis_service

router = APIRouter()
REDIS_HOTSEARCH_KEY = RedisKeyPrefix.WEIBO_HOT_SEARCH
REDIS_HOT_ARTICLE_KEY = RedisKeyPrefix.WEIBO_HOT_ARTICLE


@router.post("/scripts_terms", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
async def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    if (body.weibo_url and body.weibo_mid):
        # 如果要从微博热搜获取微博信息
        logger.info(f"开始获取实时微博热搜话题 {body.weibo_url} 【{body.weibo_title}】")
        redis_service = get_redis_service(request)
        cached_data = await redis_service.get(REDIS_HOT_ARTICLE_KEY.format(body.weibo_mid))  # 使用 await 关键字调用异步方法
        if cached_data:
            logger.success(f"获取微博热搜话题【{body.weibo_title}】缓存成功")
            weibo_article_data = json.loads(cached_data)
        else:
            weibo_article_data = await fetch_hot_article(body.weibo_mid, body.weibo_url)
            logger.success(f"实时获取微博热搜话题:{body.weibo_title} 成功")
            # 将数据缓存到 Redis 1天更新一次
            await redis_service.set(REDIS_HOT_ARTICLE_KEY.format(body.weibo_mid),
                                    json.dumps(weibo_article_data, ensure_ascii=False),
                                    expire=RedisExpireTime.ONE_DAY)
            logger.success(f"{body.weibo_mid} 微博热搜话题 {body.weibo_title} 保存redis成功.")
        # 获取微博数据内容条数 影响ai分析微博内容
        get_content_counts = 5
        weibo_summary = generate_weibo_summary(weibo_article_data, get_content_counts)  # 假设需要获取5条评论
        # 把微博热搜作为视频主题输入
        body.video_subject = weibo_summary
    video_script, video_terms, video_title = llm.generate_script_and_terms(video_subject=body.video_subject,
                                                                           language=body.video_language,
                                                                           paragraph_number=body.paragraph_number,
                                                                           video_category=body.video_category,
                                                                           amount=body.amount,
                                                                           word_count=body.word_count)
    response = {
        "video_title": video_title,
        "video_script": video_script,
        "video_terms": video_terms
    }
    return Success(data=response)


@router.post("/inspire_scripts_terms", response_model=VideoScriptResponse, summary="通过文案灵感类别为视频创建脚本以及获取对应的关键词")
async def generate_video_script_and_terms_by_inspire(request: Request, body: VideoScriptRequest):
    logger.info("Generating video by inspire，body is {}".format(body))
    video_script, video_terms, video_title = llm.generate_script_and_terms_by_inpire(video_inspire=body.video_inspire,
                                                                                     video_inspire_keyword=body.video_inspire_keyword,
                                                                                     paragraph_number=body.paragraph_number,
                                                                                     amount=body.amount,
                                                                                     word_count=body.word_count)
    response = {
        "video_title": video_title,
        "video_script": video_script,
        "video_terms": video_terms
    }
    return Success(data=response)


@router.post("/refine-scripts", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    origin_script = body.origin_script
    video_category = body.video_category
    word_count = body.word_count
    refine_script = llm.refine_scripts(original_script=origin_script, video_category=video_category,
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
    continue_script = llm.continue_scripts(original_script=origin_script, video_category=video_category,
                                           word_count=word_count)
    response = {
        "video_script": continue_script,

    }
    return Success(data=response)


@router.get("/hot-spot", response_model=VideoScriptResponse, summary="搜索新闻热点")
async def get_hot_spot(request: Request):
    redis_service = get_redis_service(request)
    cached_data = await redis_service.get(REDIS_HOTSEARCH_KEY)  # 使用 await 关键字调用异步方法
    if cached_data:
        logger.info("获取微博热搜数据redis缓存")
        hotsearch_data = json.loads(cached_data)
    else:
        hotsearch_data = await get_weibo_hotsearch()
        if hotsearch_data:
            # 将数据缓存到 Redis
            await redis_service.set(REDIS_HOTSEARCH_KEY, json.dumps(hotsearch_data, ensure_ascii=False),
                                    expire=RedisExpireTime.THIRTY_MINUTES)
    return Success(data=hotsearch_data)
