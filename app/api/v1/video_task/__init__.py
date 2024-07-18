# -- coding: utf-8 --
# @Time : 2024/7/14 10:48
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : __init__.py.py
# @Software: PyCharm
from fastapi import APIRouter

from .video_task import router

task_router = APIRouter()
task_router.include_router(router, tags=["视频任务模块"])

__all__ = ["task_router"]