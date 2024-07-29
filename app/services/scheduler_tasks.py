# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py

import json
import traceback
import tracemalloc
from typing import List

import objgraph
import psutil
from fastapi import FastAPI
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.manager.redis_manager import redis_taskmanager
from app.schemas.movies import HotSearchItem, VideoParams, WeiboArticleData
from app.services import video_controller
from app.services.factory import llm_generator
from app.services.hotspot.weibo_article import fetch_hot_article, save_weibo_article_and_update_data, \
    generate_weibo_summary
from app.services.hotspot.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import redis_instance
from app.utils import utils
from app.utils.uploader.examples.upload_video_to_douyin import auto_upload_douyin


class SchedulerTasks:
    @staticmethod
    async def publish_videos(app: FastAPI):
        logger.info("检测自动生成视频待发布视频任务")
        while True:
            task_id = await redis_instance.lpop("video_publish_queue")
            if task_id:
                await auto_upload_douyin(task_id.decode("utf-8"))
            else:
                logger.info("当前没有待自动发布的视频任务")
                break
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
            await redis_instance.set(RedisKeyPrefix.WEIBO_HOT_SEARCH,
                                     json.dumps([item.dict() for item in hotsearch_data], ensure_ascii=False),
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

    @staticmethod
    async def generate_video_by_weibo_hotspot():
        logger.info("Generating video by weibo hotspot check begin")
        # 当前生成的视频数量 不能全部生成
        generate_counts = 0
        # 每次定时任务计划生成几个视频
        target_generate_max = 50
        # 获取已存在的微博热搜列表
        weibo_artcle_list: List[str] = await redis_instance.get_keys(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format("*"))
        for weibo_artcle_title in weibo_artcle_list:
            weibo_article_cache = await redis_instance.get(weibo_artcle_title)
            weibo_article_data = WeiboArticleData(**json.loads(weibo_article_cache))
            # 检查是否有 'is_generated' 属性且其值为 False
            if hasattr(weibo_article_data, "is_generated") and not getattr(weibo_article_data, "is_generated"):
                # 取其中第一个未生成热门视频的热搜话题进行生成文案
                # 获取微博数据内容条数 影响ai分析微博内容
                logger.info(f"启动自动生成视频任务：{weibo_artcle_title}")
                get_content_counts = 5
                weibo_summary = generate_weibo_summary(weibo_article_data, get_content_counts)  # 假设需要获取5条评论
                # 把微博热搜作为视频主题输入

                params = {"video_subject": weibo_summary,
                          "word_count": 300,
                          "video_category": "opinion_sharing",
                          "video_terms": [],
                          "video_aspect": "16:9",
                          "video_concat_mode":
                              "random",
                          "video_clip_duration": 10,
                          "video_count": 1,
                          "video_source": "pixabay",
                          "video_materials": [],
                          "video_language": "auto-detect",
                          "voice_name": "zh-CN-YunjianNeural",
                          "voice_volume": 1,
                          "bgm_type": "random",
                          "bgm_file": "",
                          "bgm_volume": 0.1,
                          "subtitle_enabled": True,
                          "subtitle_position": "bottom",
                          "font_name": "MicrosoftYaHeiBold.ttc",
                          "text_fore_color": "#ffffff",
                          "text_background_color": "#39C186FF",
                          "font_size": 65,
                          "stroke_color": "#1e1e1b",
                          "stroke_width": 1.5,
                          "n_threads": 8,
                          "paragraph_number": 4,
                          "amount": 5,
                          "weibo_mid": weibo_article_data.weibo_mid,
                          "weibo_title": weibo_artcle_title.replace("weibo_hot_article:", "")}
                body = VideoParams(**params)
                logger.info(f"开始自动生成文案")
                video_script, video_terms, video_title = llm_generator.generate_script_and_terms(
                    video_subject=body.video_subject,
                    language=body.video_language,
                    paragraph_number=body.paragraph_number,
                    video_category=body.video_category,
                    amount=body.amount,
                    word_count=body.word_count)
                body.video_terms = video_terms
                body.video_script = video_script
                body.video_subject = video_title

                # 生成视频后自动发布
                task_id = utils.get_task_id()
                task = {
                    "task_id": task_id,
                    "params": body.dict(),
                }
                try:
                    # 设置为自动生成视频 方便生成视频结束后刷新该微博文章已保存的状态
                    body.auto_generate = True
                    await redis_instance.update_task(task_id)
                    await redis_taskmanager.add_task(video_controller.start, task_id=task_id, params=body)
                    logger.info(f"自动生成视频任务已创建: {utils.to_json(task)}\ntask_id is {task_id} ")
                    generate_counts += 1
                    if generate_counts > target_generate_max:
                        break
                except Exception as e:
                    logger.error("生成视频失败")
                    logger.error(f"{traceback.format_exc()}")
        logger.info("Generating video by weibo hotspot check over")
    @staticmethod
    def log_memory_usage():
        """使用 psutil 定期记录内存使用情况"""
        process = psutil.Process()
        mem_info = process.memory_info()
        logger.info(
            f"Memory usage: RSS = {mem_info.rss / (1024 * 1024):.2f} MB, VMS = {mem_info.vms / (1024 * 1024):.2f} MB")

    @staticmethod
    def log_tracemalloc_snapshot():
        """使用 tracemalloc 监控内存分配"""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        logger.info("[ Top 10 memory usage ]")
        for stat in top_stats[:10]:
            logger.info(stat)

    @staticmethod
    def show_most_common_types():
        """使用 memory_profiler 监控特定函数的内存使用情况，并使用 objgraph 查找内存泄漏。"""
        objgraph.show_most_common_types()
