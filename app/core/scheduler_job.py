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
    scheduler.add_job(SchedulerTasks.get_weibo_hotsearch, 'interval', minutes=15)
    # # 获取微博热搜内容图片评论视频等素材
    scheduler.add_job(SchedulerTasks.get_weibo_articles_to_cache, 'interval', minutes=5,
                      next_run_time=datetime.now() + timedelta(seconds=135))
    # 自动生成微博热搜视频的定时任务
    scheduler.add_job(SchedulerTasks.generate_video_by_weibo_hotspot, 'interval', minutes=6,
                      next_run_time=datetime.now() + timedelta(seconds=55))
    # 发布视频的账号  随机选择进行发布，同一个task不可多个账号发布同个平台
    account_list = [
        {"account_name": "account-jiahua.json",
         "platform": ["douyin"],
         },

        {"account_name": "account-chao.json",
         "platform": ["xigua"],
         },
    ]

    # # 自动发布视频的定时任务
    scheduler.add_job(SchedulerTasks.publish_videos, 'interval', minutes=2,
                      next_run_time=datetime.now() + timedelta(seconds=35), args=[account_list])
    # # 自动填入发布定时任务
    # scheduler.add_job(SchedulerTasks.enqueue_tasks, CronTrigger(hour=8, minute=50),
    #                   next_run_time=datetime.now() + timedelta(seconds=20))
    #
    # scheduler.add_job(SchedulerTasks.clear_tasks, CronTrigger(hour=8, minute=49),
    #                   next_run_time=datetime.now() + timedelta(seconds=15))
    # 更新抖音cookies
    account_list = [i.get('account_name') for i in account_list if i.get('platform') == 'douyin']
    scheduler.add_job(SchedulerTasks.get_douoyin_cookies, CronTrigger(hour=8, minute=49),
                      next_run_time=datetime.now() + timedelta(seconds=15), args=[account_list])
    # 更新西瓜cookies
    account_list = [i.get('account_name') for i in account_list if i.get('platform') == 'xigua']
    scheduler.add_job(SchedulerTasks.get_xigua_cookies, CronTrigger(hour=8, minute=49),
                      next_run_time=datetime.now() + timedelta(seconds=15), args=[account_list])
    # 更新视频号cookies
    # scheduler.add_job(SchedulerTasks.get_tencent_cookie, 'interval', inutes=3,
    #                                         next_run_time=datetime.now() + timedelta(seconds=15))

    scheduler.start()
