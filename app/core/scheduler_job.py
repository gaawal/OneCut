# -- coding: utf-8 --
# @Time : 2024/6/25 09:42
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_job.py
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.scheduler_tasks import SchedulerTasks

scheduler = AsyncIOScheduler()


def register_scheduler_job(app):
    # 初始化并启动定时任务 指定时间 用于调试 CronTrigger(hour=00, minute=15)
    # scheduler.add_job(SchedulerTasks.log_memory_usage, 'interval', seconds=31)
    # scheduler.add_job(SchedulerTasks.log_tracemalloc_snapshot, 'interval', seconds=33)
    # scheduler.add_job(SchedulerTasks.show_most_common_types, 'interval', seconds=37)
    # 刷新微博热搜榜单
    scheduler.add_job(SchedulerTasks.get_weibo_hotsearch, 'interval', minutes=15,
                      next_run_time=datetime.now() + timedelta(seconds=60))
    # 获取微博热搜内容图片评论信息
    scheduler.add_job(SchedulerTasks.get_weibo_articles_to_cache, 'interval', seconds=241,
                      next_run_time=datetime.now() + timedelta(seconds=120))
    # 自动生成微博热搜视频的定时任务
    scheduler.add_job(SchedulerTasks.generate_video_by_weibo_hotspot, 'interval', seconds=301,
                      next_run_time=datetime.now() + timedelta(seconds=111))
    # 自动发布视频的定时任务
    scheduler.add_job(SchedulerTasks.publish_videos, 'interval', minutes=10,
                      next_run_time=datetime.now() + timedelta(seconds=35))
    # 更新抖音cookies
    # scheduler.add_job(SchedulerTasks.get_douoyin_cookies, 'interval', seconds=5)
    # 更新视频号cookies
    # scheduler.add_job(SchedulerTasks.get_tencent_cookie, 'interval', seconds=5)

    scheduler.start()
