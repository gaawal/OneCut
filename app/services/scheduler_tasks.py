# -- coding: utf-8 --
# @Time : 2024/6/29 14:09
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_tasks.py

import json
import random
import traceback
import tracemalloc
from typing import List

import objgraph
import psutil
from loguru import logger

from app.constant.redis_const import RedisExpireTime, RedisKeyPrefix
from app.constant.video_const import TaskState, TaskDetailState, CollectStatus, VIDEO_STYLE_MAP
from app.controllers.video_task import task_controller
from app.manager.redis_manager import redis_taskmanager
from app.models import TaskModel, get_platform_status, update_platform_status
from app.schemas.movies import HotSearchItem, VideoParams, WeiboArticleData
from app.services import video_controller
from app.services.factory import llm_generator, video_splitter
from app.services.factory.video_splitter import VideoSplitter
from app.utils.crawler.weibo_crawler.get_weibo_cookie import get_weibo_cookies
from app.utils.crawler.weibo_crawler.weibo_article import fetch_hot_article, save_weibo_article_and_update_data, \
    generate_weibo_summary

from app.utils.crawler.weibo_crawler.weibo_hotsearch import get_weibo_hotsearch
from app.services.redis_service import redis_instance
from app.services.video_controller import save_task_state
from app.utils import utils
from app.utils.crawler.weibo_crawler.weibo_video import WeiboCrawler
from app.utils.uploader.examples.get_douyin_cookie import get_douoyin_cookies
from app.utils.uploader.examples.get_tencent_cookie import get_tencent_cookie
from app.utils.uploader.examples.get_xigua_cookie import get_xigua_cookies
from app.utils.uploader.examples.upload_video_to_douyin import auto_upload_douyin
from app.utils.uploader.examples.upload_video_to_tencent import auto_upload_weixin
from app.utils.uploader.examples.upload_video_to_xigua import auto_upload_xigua
from app.utils.utils import generate_md5_id

video_splitter = VideoSplitter()
weibo_crawler = WeiboCrawler()


class SchedulerTasks:
    @staticmethod
    def get_xigua_cookies(account_list):
        logger.info(f"检测西瓜账号cookie {account_list}")
        get_xigua_cookies(account_list)

    @staticmethod
    async def clear_tasks():
        """清理所有任务"""
        clear_list = []
        key = 'video_publish_queue'
        for _ in clear_list:
            task_id = await redis_instance.lpop(key)
            logger.info(f"清理任务id: {task_id}")

    @staticmethod
    async def enqueue_tasks():
        tasks_list = []
        key = 'video_publish_queue'
        queue_items = await redis_instance.get_list(key)
        logger.info(f"当前待发布视频任务有: {queue_items}")

        for task_id in tasks_list:
            if task_id not in queue_items:
                await redis_instance.rpush(key, task_id)
                logger.info(f"手工加入发布任务成功,task_id={task_id}")
        queue_items = await redis_instance.get_list(key)
        logger.info(f"当前待发布视频任务有: {queue_items}")

    @staticmethod
    async def publish_videos(account_list):
        video_publish_queue = "video_publish_queue"
        while True:
            task_id = await redis_instance.lpop(video_publish_queue)
            logger.info("发布视频任务检测开始")
            try:
                if task_id:
                    task_obj: TaskModel = await task_controller.get_by_task_id(task_id)
                    # 判断该任务是否发布成功状态了，如果没有才能进入发布流程
                    if task_obj.state != TaskState.PUBLISH_OK or task_obj.state != TaskState.PROCESSING:
                        # 打印当前待发布队列中的任务ID数组
                        is_uploaded = False
                        await redis_instance.print_queue("video_publish_queue")
                        logger.info(f"存在生成视频待发布视频任务,task_id：{task_obj.task_id}")
                        # 刷新待发布状态
                        await save_task_state(task_id, TaskState.PUBLISHING, 100, TaskDetailState.PUBLISHING)
                        # 获取平台状态
                        logger.info(f"获取当前视频各平台发布状态")
                        weixin_status = await get_platform_status(task_obj.task_id, "weixin")
                        douyin_status = await get_platform_status(task_obj.task_id, "douyin")
                        xigua_status = await get_platform_status(task_obj.task_id, "xigua")
                        logger.info(f"Weixin 状态: {weixin_status}")
                        logger.info(f"Douyin 状态: {douyin_status}")
                        account = random.choice(account_list)
                        account_name: str = account.get('account_name')
                        platform: list = account.get('platform')
                        logger.info(f"随机选取上传账号为{account_name},需要发布的平台:{platform}")
                        if weixin_status != TaskDetailState.UPLOAD_OK and 'weixin' in platform:
                            try:
                                logger.info(f"发布视频至视频号")
                                is_uploaded = await auto_upload_weixin(task_id, account_name)
                                await update_platform_status(task_obj.task_id, "weixin", TaskDetailState.UPLOAD_OK)
                                logger.success(f"发布视频至视频号完成，刷新成功状态")
                                weixin_status = TaskDetailState.UPLOAD_OK
                            except:
                                weixin_status = TaskDetailState.UPLOAD_FAILED
                        if douyin_status != TaskDetailState.UPLOAD_OK and 'douyin' in platform:
                            try:
                                logger.info(f"发布视频至抖音")
                                is_uploaded = await auto_upload_douyin(task_id, account_name)
                            except Exception as e:
                                is_uploaded = False
                                logger.info(f"发布存在异常，发布任务重新加入队列")
                                queue_items = await redis_instance.get_list(video_publish_queue)
                                if task_id not in queue_items:
                                    await redis_instance.rpush(video_publish_queue, task_id)
                                    logger.info(f"手工加入发布任务成功,task_id={task_id}")
                                    queue_items = await redis_instance.get_list(video_publish_queue)
                                    logger.info(f"当前待发布视频任务有: {queue_items}")

                        if xigua_status != TaskDetailState.UPLOAD_OK and 'xigua' in platform:
                            try:
                                logger.info(f"发布视频至西瓜")
                                is_uploaded = await auto_upload_xigua(task_id, account_name)
                            except Exception as e:
                                is_uploaded = False
                                logger.info(f"发布存在异常，发布任务重新加入队列")
                                queue_items = await redis_instance.get_list(video_publish_queue)
                                if task_id not in queue_items:
                                    await redis_instance.rpush(video_publish_queue, task_id)
                                    logger.info(f"手工加入发布任务成功,task_id={task_id}")
                                    queue_items = await redis_instance.get_list(video_publish_queue)
                                    logger.info(f"当前待发布视频任务有: {queue_items}")
                        if is_uploaded:
                            await update_platform_status(task_obj.task_id, "douyin", TaskDetailState.UPLOAD_OK)
                            logger.success(f"发布视频至抖音完成，刷新成功状态")
                            logger.success("所有平台视频都发布成功，任务已完成！")
                            # 从 Redis 队列中删除任务ID
                            # 刷新发布成功状态
                            await save_task_state(task_id, TaskState.PUBLISH_OK, 100, TaskDetailState.PUBLISH_OK)
                            await redis_instance.lrem("video_publish_queue", 0, task_id)
                        break
                    else:
                        logger.info("存在已发布成功或发布中的视频任务,不需要重新发布task_id：", task_id)
                else:
                    logger.info("发布视频任务检测结束")
                    break
            except Exception as e:
                logger.error(traceback.format_exc())
                # 刷新发布失败状态
                await save_task_state(task_id, TaskState.PUBLISH_FAILED, 100, TaskDetailState.PUBLIS_FAILED)

    @staticmethod
    async def get_weibo_hotsearch():
        hotsearch_data: List[HotSearchItem] = await get_weibo_hotsearch()
        # 将数据缓存到 Redis
        if hotsearch_data:
            for i, hotsearch in enumerate(hotsearch_data):
                # 如果已经采集过了，更新采集状态
                if await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(hotsearch.title)):
                    hotsearch.collect_status = CollectStatus.COLLECT_OK
                    hotsearch_data[i] = hotsearch
            await redis_instance.set(RedisKeyPrefix.WEIBO_HOT_SEARCH,
                                     json.dumps([item.dict() for item in hotsearch_data], ensure_ascii=False),
                                     expire=RedisExpireTime.ONE_HOUR)

    @staticmethod
    async def get_weibo_articles_to_cache():
        """获取微博热搜评论、图片、视频素材等"""
        try:
            cached_data = await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_SEARCH)  # 使用 await 关键字调用异步方法
            if cached_data:
                hotsearch_data = json.loads(cached_data)
                for i, item in enumerate(hotsearch_data):
                    title = item.get('title')
                    url = item.get('url')
                    if not await redis_instance.get(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format(title)):
                        weibo_mid = generate_md5_id(url)
                        target_url = f'{url}'
                        weibo_article_data = WeiboArticleData(
                            weibo_mid=weibo_mid,
                            url=target_url,
                        )
                        logger.info(f"微博热搜需要采集信息：{title} ")
                        # 采集微博热搜视频
                        logger.info(f"采集微博热搜视频：{title} ")
                        weibo_video_paths = await weibo_crawler.collect_videos(title, weibo_mid)
                        if weibo_video_paths:
                            logger.success(f"微博热搜视频采集成功：{weibo_video_paths} ")
                            weibo_article_data.videos = weibo_video_paths
                            await save_weibo_article_and_update_data(title, weibo_article_data,
                                                                     CollectStatus.COLLECTING)
                            for video_path in weibo_video_paths:
                                logger.info(f"微博热搜视频开始智能分割片段：{video_path} ")
                                saved_paths = await video_splitter.process_video(video_path)
                                if saved_paths:
                                    logger.info(f"保存智能分割片段结果：{saved_paths} ")
                                    weibo_article_data.split_videos.extend(saved_paths)
                            await save_weibo_article_and_update_data(title, weibo_article_data,
                                                                     CollectStatus.COLLECTING)
                        else:
                            logger.warning(f"微博热搜视频采集结果为空：{title}")
                        await save_weibo_article_and_update_data(title, weibo_article_data)
                        logger.info(f"采集微博热搜图片评论素材：{title} ")
                        weibo_article_data: WeiboArticleData = await fetch_hot_article(weibo_article_data, weibo_mid,
                                                                                       target_url)
                        await save_weibo_article_and_update_data(title, weibo_article_data, CollectStatus.COLLECT_OK)
                        logger.success(f"采集微博热搜图片评论素材成功！话题：{title} ")
                        break
        except Exception as e:
            logger.error(f"{traceback.format_exc()}")

    @staticmethod
    async def generate_video_by_weibo_hotspot():
        logger.info("扫描微博热搜生成视频任务启动...")
        # 当前生成的视频数量 不能全部生成
        generate_counts = 0
        # 每次定时任务计划生成几个视频
        target_generate_max = 1
        # 获取已存在的微博热搜列表
        weibo_artcle_list: List[str] = await redis_instance.get_keys(RedisKeyPrefix.WEIBO_HOT_ARTICLE.format("*"))
        for weibo_artcle_title in weibo_artcle_list:
            weibo_article_cache = await redis_instance.get(weibo_artcle_title)
            weibo_article_data = WeiboArticleData(**json.loads(weibo_article_cache))
            # 检查是否有 'is_generated' 属性且其值为 False
            if hasattr(weibo_article_data, "is_generated") and not getattr(weibo_article_data,
                                                                           "is_generated") and weibo_article_data.articles:
                # 取其中第一个未生成热门视频的热搜话题进行生成文案
                # 获取微博数据内容条数 影响ai分析微博内容
                logger.info(f"启动自动生成视频任务：{weibo_artcle_title}")

                weibo_summary = generate_weibo_summary(weibo_article_data)  # 假设需要获取5条评论
                # 随机选择发布的视频文案风格
                choose_categorys = list(VIDEO_STYLE_MAP.keys())
                choose_bgms = ['麦克阿瑟进行曲', "i'll Do It"]
                # 把微博热搜作为视频主题输入
                params = {"video_subject": weibo_summary,
                          "word_count": 300,
                          "video_category": random.choice(choose_categorys),
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
                          "bgm_file": random.choice(choose_bgms),
                          "bgm_volume": 0.3,
                          "subtitle_enabled": True,
                          "subtitle_position": "bottom",
                          "font_name": "MicrosoftYaHeiBold.ttc",
                          "text_fore_color": "#ffffff",
                          "text_background_color": "#39C186FF",
                          "font_size": 65,
                          "stroke_color": "#1e1e1b",
                          "stroke_width": 1.5,
                          "paragraph_number": 4,
                          "amount": 5,
                          "weibo_mid": weibo_article_data.weibo_mid,
                          "weibo_title": weibo_artcle_title.replace("weibo_hot_article:", "")}
                body = VideoParams(**params)
                logger.info(f"开始自动生成文案,热门话题内容 {weibo_summary}")
                video_script, video_terms, video_title, video_tags = llm_generator.generate_script_and_terms(
                    video_subject=body.video_subject,
                    language=body.video_language,
                    paragraph_number=body.paragraph_number,
                    video_category=body.video_category,
                    amount=body.amount,
                    word_count=body.word_count)
                body.video_terms = video_terms
                body.video_script = video_script
                body.video_subject = video_title
                body.video_tags = video_tags

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
                    logger.info(f"自动生成视频任务已创建,task_id:{task_id} ")
                    generate_counts += 1
                    if generate_counts >= target_generate_max:
                        break
                except Exception as e:
                    logger.error("生成视频失败")
                    logger.error(f"{traceback.format_exc()}")
        logger.info("扫描微博热搜生成视频任务结束")

    @staticmethod
    def get_douoyin_cookies(account_list):

        logger.info("检测抖音账号cookie,{}".format(account_list))
        get_douoyin_cookies(account_list)

    @staticmethod
    def get_tencent_cookie():
        logger.info("检测微信视频号cookie")
        get_tencent_cookie()

    @staticmethod
    async def get_weibo_cookie():
        logger.info("检测微博cookie")
        await get_weibo_cookies()

    @staticmethod
    def log_memory_usage():
        """使用 psutil 定期记录内存使用情况"""
        process = psutil.Process()
        mem_info = process.memory_info()
        logger.info(
            f"当前内存使用大小: RSS = {mem_info.rss / (1024 * 1024):.2f} MB, 虚拟内存大小: VMS = {mem_info.vms / (1024 * 1024):.2f} MB")

    @staticmethod
    def log_tracemalloc_snapshot():
        """使用 tracemalloc 监控内存分配"""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        logger.info("[ Top 10 内存使用情况 ]")
        for stat in top_stats[:10]:
            logger.info(stat)

    @staticmethod
    def show_most_common_types():
        """使用 memory_profiler 监控特定函数的内存使用情况，并使用 objgraph 查找内存泄漏。"""
        objgraph.show_most_common_types()
