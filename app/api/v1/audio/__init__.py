# -- coding: utf-8 --
# @Time : 2024/5/27 12:22
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : __init__.py.py

from fastapi import APIRouter

from .audio import router

audio_router = APIRouter()
audio_router.include_router(router, tags=["音频生成模块"])

__all__ = ["audio_router"]