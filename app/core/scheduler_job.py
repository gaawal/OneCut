# -- coding: utf-8 --
# @Time : 2024/6/25 09:42
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_job.py
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.scheduler_tasks import SchedulerTasks

scheduler = AsyncIOScheduler()


def register_scheduler_job(app):
    # 刷新微博热搜榜单
    scheduler.add_job(SchedulerTasks.get_weibo_hotsearch, 'interval', minutes=15)
    # # # 获取微博热搜内容图片评论信息
    scheduler.add_job(SchedulerTasks.get_weibo_articles_to_cache, 'interval', minutes=5,
                      next_run_time=datetime.now() + timedelta(seconds=25))
    scheduler.start()
