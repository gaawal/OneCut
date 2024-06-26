# -- coding: utf-8 --
# @Time : 2024/5/27 12:22
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : __init__.py.py
# @Software: PyCharm
from fastapi import APIRouter

from .video import router

video_router = APIRouter()
video_router.include_router(router, tags=["视频生成模块"])

__all__ = ["video_router"]