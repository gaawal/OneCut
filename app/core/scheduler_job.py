# -- coding: utf-8 --
# @Time : 2024/6/25 09:42
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : scheduler_job.py
# @Software: PyCharm
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.scheduler_tasks import SchedulerTasks

scheduler = AsyncIOScheduler()

def register_scheduler_job(app):
    # 初始化并启动定时任务
    scheduler.add_job(SchedulerTasks.get_weibo_hotsearch, 'interval', minutes=29, args=[app])
    scheduler.start()