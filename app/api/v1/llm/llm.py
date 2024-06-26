# -- coding: utf-8 --
# @Time : 2024/5/27 10:50
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : llm.py
# @Software: PyCharm
import json

from fastapi import APIRouter, Request
from loguru import logger

from app.schemas import Success
from app.schemas.movies import VideoScriptResponse, VideoScriptRequest
from app.services import llm
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.utils.redis import get_redis_service

router = APIRouter()
REDIS_HOTSEARCH_KEY = "weibo_hotsearch"


@router.post("/scripts_terms", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
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


@router.post("/refine-scripts", response_model=VideoScriptResponse, summary="为视频创建脚本以及获取对应的关键词")
def generate_video_script_and_terms(request: Request, body: VideoScriptRequest):
    origin_script = body.origin_script
    video_category = body.video_category
    word_count = body.word_count
    refine_script = llm.refine_scripts(original_script=origin_script, video_category=video_category,word_count=word_count
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
    continue_script = llm.continue_scripts(original_script=origin_script, video_category=video_category,word_count=word_count
                                       )
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
        hotsearch_data = await get_weibo_hotsearch(request.app)
    return Success(data=hotsearch_data)
