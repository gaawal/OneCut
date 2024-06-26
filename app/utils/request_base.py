# -- coding: utf-8 --
# @Time : 2024/5/27 11:52
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : request_base.py
# @Software: PyCharm
from uuid import uuid4

from fastapi import Request

from app.settings import movies_config
from app.models.exception import HttpException


def get_task_id(request: Request):
    task_id = request.headers.get('x-task-id')
    if not task_id:
        task_id = uuid4()
    return str(task_id)


def get_api_key(request: Request):
    api_key = request.headers.get('x-api-key')
    return api_key


def verify_token(request: Request):
    token = get_api_key(request)
    if token != movies_config.app.get("api_key", ""):
        request_id = get_task_id(request)
        request_url = request.url
        user_agent = request.headers.get('user-agent')
        raise HttpException(task_id=request_id, status_code=401, message=f"invalid token: {request_url}, {user_agent}")
