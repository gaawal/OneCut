# -- coding: utf-8 --
# @Time : 2024/7/14 10:46
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : tasks.py

from tortoise import fields
from .base import BaseModel, TimestampMixin


class Task(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True)
    user_id = fields.IntField(description="用户ID")
    task_id = fields.CharField(max_length=50, unique=True, description="任务ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    progress = fields.IntField(default=0, description="任务进度")
    state = fields.CharField(max_length=20, description="任务状态")
    draft_content = fields.JSONField(description="草稿内容")

    class Meta:
        table = "task"

    class PydanticMeta:
        exclude = ["id"]
