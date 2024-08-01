# -- coding: utf-8 --
# @Time : 2024/7/14 10:46
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : task_model.py

from tortoise import fields
from .base import BaseModel, TimestampMixin


class TaskModel(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True)
    user_id = fields.IntField(description="用户ID")
    task_id = fields.CharField(max_length=50, unique=True, description="任务ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    progress = fields.IntField(default=0, description="任务进度")
    state = fields.CharField(max_length=255, description="任务状态")
    detail_state = fields.CharField(max_length=255, description="任务详细状态")
    platform_status = fields.JSONField(default=dict, description="各平台任务详细状态")
    draft_content = fields.JSONField(description="草稿内容")

    class Meta:
        table = "task"

    class PydanticMeta:
        exclude = ["id"]

async def update_platform_status(task_id: str, platform: str, status: str):
    task_obj = await TaskModel.get(task_id=task_id)
    platform_status = task_obj.platform_status
    platform_status[platform] = status
    task_obj.platform_status = platform_status
    await task_obj.save()

async def get_platform_status(task_id: str, platform: str):
    task_obj = await TaskModel.get(task_id=task_id)
    return task_obj.platform_status.get(platform)

