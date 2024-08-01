# -- coding: utf-8 --
# @Time : 2024/7/14 10:50
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : tasks.py

from pydantic import BaseModel
from typing import Optional, Dict


class TaskBase(BaseModel):
    user_id: int
    task_id: str
    progress: int
    state: str
    detail_state: Optional[Dict] = None
    draft_content: Optional[Dict] = None


class TaskCreate(TaskBase):
    def create_dict(self):
        return self.dict(exclude_unset=True)


class TaskUpdate(TaskBase):
    id: int
    detail_state: Optional[str] = None
    failure_reason: Optional[str] = None

    def update_dict(self):
        return self.dict(exclude_unset=True)
