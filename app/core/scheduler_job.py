# -- coding: utf-8 --
# @Time : 2024/6/25 09:42
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_job.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.scheduler_tasks import SchedulerTasks

scheduler = AsyncIOScheduler()

def register_scheduler_job(app):
    # 初始化并启动定时任务 指定时间 用于调试 CronTrigger(hour=00, minute=15)
    scheduler.add_job(SchedulerTasks.get_weibo_hotsearch, 'interval', minutes=60)
    scheduler.add_job(SchedulerTasks.get_weibo_articles_to_cache, 'interval', minutes=30)
    # 自动生成文案的定时任务间隔时间请大于平均视频生成时间
    scheduler.add_job(SchedulerTasks.generate_video_by_weibo_hotspot,CronTrigger(hour=00, minute=17))
    scheduler.start()