# -- coding: utf-8 --
# @Time : 2024/7/14 10:47
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : tasks.py

from typing import List, Optional

from app.core.crud import CRUDBase
from app.models.tasks import Task
from app.schemas.video_task import TaskCreate, TaskUpdate

class TaskController(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def __init__(self):
        super().__init__(model=Task)

    async def get_by_task_id(self, task_id: str) -> Optional[Task]:
        return await self.model.filter(task_id=task_id).first()

    async def get_by_user_id(self, user_id: int) -> List[Task]:
        return await self.model.filter(user_id=user_id).all()

    async def create(self, obj_in: TaskCreate) -> Task:
        obj = await super().create(obj_in.create_dict())
        return obj

    async def update(self, obj_in: TaskUpdate) -> Task:
        return await super().update(id=obj_in.id, obj_in=obj_in.update_dict())

task_controller = TaskController()
