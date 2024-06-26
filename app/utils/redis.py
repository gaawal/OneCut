# -- coding: utf-8 --
# @Time : 2024/6/24 00:25
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : redis.py
# @Software: PyCharm
from fastapi import Request
from app.services.redis_service import RedisService

def get_redis_service(request: Request) -> RedisService:
    return RedisService(request.app.state.redis)