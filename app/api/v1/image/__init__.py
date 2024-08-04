# -- coding: utf-8 --
# @Time : 2024/8/3 12:25
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : __init__.py.py
# @Software: PyCharm
from fastapi import APIRouter

from .image import router

image_router = APIRouter()
image_router.include_router(router, tags=["视频生成模块"])

__all__ = ["image_router"]