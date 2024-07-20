# -- coding: utf-8 --
# @Time : 2024/5/27 10:50
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : __init__.py.py

from fastapi import APIRouter

from .llm import router

llm_router = APIRouter()
llm_router.include_router(router, tags=["llm文案生成模块"])

__all__ = ["llm_router"]